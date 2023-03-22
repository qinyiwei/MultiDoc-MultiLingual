from nltk import sent_tokenize
from tqdm import tqdm
from rouge_score import rouge_scorer, scoring
import os
import json
import re
import csv
import click
from tqdm import tqdm
import random

lang_to_rouge_lang = {
    "chinese": "chinese",
    "cantonese": "chinese",
    "EN": "english",
    "RU": "russian",
    "VI": "vietnamese",
    "CZ": "czech",
    "UA": "ukrainian",
    "PL": "polish",
}


def zng(paragraph):
    for sent in re.findall(u'[^!?。\.\!\?]+[!?。\.\!\?]?', paragraph, flags=re.U):
        yield sent


def calculate_rouge(
    pred_lns,
    tgt_lns,
    use_stemmer=True,
    bootstrap_aggregation=True,
    rouge_lang=None,
):
    scorer = rouge_scorer.RougeScorer(
        ['rouge1', 'rouge2', 'rougeL'],
        use_stemmer=use_stemmer,
        lang=rouge_lang,
    )
    aggregator = scoring.BootstrapAggregator()
    for pred, tgt in zip(tgt_lns, pred_lns):
        # rougeLsum expects "\n" separated sentences within a summary
        scores = scorer.score(pred, tgt)
        aggregator.add_scores(scores)

    if bootstrap_aggregation:
        result = aggregator.aggregate()
        return {k: round(v.mid.fmeasure * 100, 4) for k, v in result.items()}

    else:
        return aggregator._scores  # here we return defaultdict(list)


def greedy_selection(src, tgt, N, lang):
    output = []
    if lang == "chinese" or lang == "cantonese":
        src_sents = list(zng(src))
    else:
        src_sents = sent_tokenize(src)
    rouge_lang = lang_to_rouge_lang[lang]
    for i in range(N):
        max_rouge = 0
        for s in src_sents:
            rouge = calculate_rouge(["".join(output)+s], [tgt], rouge_lang)
            #cur_rouge = rouge['rouge1']+rouge["rouge2"]+rouge["rougeL"]
            cur_rouge = rouge["rouge2"]
            if cur_rouge > max_rouge:
                max_rouge = cur_rouge
                max_sent = s
        if max_rouge == 0:
            break
        output.append(max_sent)
        src_sents.remove(max_sent)
    # return output
    max_rouge = calculate_rouge(["".join(output)], [tgt])
    print(max_rouge)
    print(output)
    return max_rouge["rouge2"], output


def preprocess(orig_text):
    pos = []
    for match in re.finditer(r"\[\d+\]|（.*?）|\(.*?\)", orig_text):
        pos.append(match.span())
    if len(pos) != 0:
        text = ""
        for i in range(len(pos)):
            if i == 0:
                text += orig_text[:pos[0][0]]
            else:
                text += orig_text[pos[i-1][1]:pos[i][0]]
        text += orig_text[pos[-1][1]:]
    else:
        text = orig_text
    text = text.replace("\n", ' ')
    return text


lang_2_summary_dict = {
    "EN": "text",
    "CZ": "summary",
    "PL": "summary",
    "RU": "summary",
    "UA": "summary",
    "VI": "summary",
    "cantonese": "text",
    "chinese": "text",
}

N_SENT = 2


@click.command()
@click.option('--data-dir', required=False, type=str, help='Data directory.')
@click.option('--input-file-name', required=False, type=str, help='Input file name.')
@click.option('--lang', required=False, type=str, help='Data directory.')
@click.option('--output-dir', required=False, type=str, help='Output directory.')
def main(data_dir, input_file_name, lang, output_dir):
    data = []
    for line in open(os.path.join(data_dir, input_file_name), 'r'):
        data.append(json.loads(line))

    SUMMARY = []
    SINGLE_ORACLE_RESULT = []
    MULTI_ORACLE_RESULT = []
    LEAD_ORACLE_RESULT = []
    LEAD_RANDOM_RESULT = []
    for example in tqdm(data):
        summary = example["summary"]
        SUMMARY.append(summary)
        best_rouge = 0
        best_ref = ""
        single_oracle_result = ""
        all_ref = []
        single_oracle_result_all = []
        # single oracle
        for ref in (example['references_aug'] + example['references']):
            if 'text' in ref:
                text = ref['text'][:10000]
                all_ref.append(text)
                single_oracle_socre,  single_oracle_result_tmp = \
                    greedy_selection(text, summary, N_SENT, lang)
                single_oracle_result_all.extend(single_oracle_result_tmp)
                if single_oracle_socre > best_rouge:
                    best_ref = text
                    best_rouge = single_oracle_socre
                    single_oracle_result = single_oracle_result_tmp
        SINGLE_ORACLE_RESULT.append("".join(single_oracle_result))

        # lead oracle
        if lang == "chinese" or lang == "cantonese":
            text_sents = list(zng(best_ref))
        else:
            text_sents = sent_tokenize(best_ref)
        LEAD_ORACLE_RESULT.append("".join(text_sents[:N_SENT]))

        # multi oracle
        multi_oracle_socre,  multi_oracle_result = \
            greedy_selection(" ".join(single_oracle_result_all),
                             summary, N_SENT, lang)
        MULTI_ORACLE_RESULT.append("".join(multi_oracle_result))
        print("multi_oracle_score:{}".format(multi_oracle_socre))
        print(multi_oracle_result)

        # lead random
        if len(all_ref) == 0:
            all_ref = [""]
        ref_random = random.choice(all_ref)
        if lang == "chinese" or lang == "cantonese":
            text_sents = list(zng(ref_random))
        else:
            text_sents = sent_tokenize(ref_random)
        LEAD_RANDOM_RESULT.append("".join(text_sents[:N_SENT]))

    rouge_lang = lang_to_rouge_lang[lang]
    SINGLE_ORACLE_ROUGE = calculate_rouge(
        SINGLE_ORACLE_RESULT, SUMMARY, rouge_lang)
    MULTI_ORACLE_ROUGE = calculate_rouge(
        MULTI_ORACLE_RESULT, SUMMARY, rouge_lang)
    LEAD_ORACLE_ROUGE = calculate_rouge(
        LEAD_ORACLE_RESULT, SUMMARY, rouge_lang)
    LEAD_RANDOM_ROUGE = calculate_rouge(
        LEAD_RANDOM_RESULT, SUMMARY, rouge_lang)

    output_file_single_oracle = open(os.path.join(
        output_dir, "{}_single_oracle.jsonl".format(lang)), 'w')
    output_file_multi_oracle = open(os.path.join(
        output_dir, "{}_multi_oracle.jsonl".format(lang)), 'w')
    output_file_lead_oracle = open(os.path.join(
        output_dir, "{}_lead_oracle.jsonl".format(lang)), 'w')
    output_file_lead_random = open(os.path.join(
        output_dir, "{}_lead_random.jsonl".format(lang)), 'w')

    for result in SINGLE_ORACLE_RESULT:
        json.dump(result, output_file_single_oracle)
        output_file_single_oracle.write("\n")
    output_file_single_oracle.close()
    print("single oracle:")
    print(SINGLE_ORACLE_ROUGE)

    for result in MULTI_ORACLE_RESULT:
        json.dump(result, output_file_multi_oracle)
        output_file_multi_oracle.write("\n")
    output_file_multi_oracle.close()
    print("multi oracle:")
    print(MULTI_ORACLE_ROUGE)

    for result in LEAD_ORACLE_RESULT:
        json.dump(result, output_file_lead_oracle)
        output_file_lead_oracle.write("\n")
    output_file_lead_oracle.close()
    print("lead oracle:")
    print(LEAD_ORACLE_ROUGE)

    for result in LEAD_RANDOM_RESULT:
        json.dump(result, output_file_lead_random)
        output_file_lead_random.write("\n")
    output_file_lead_random.close()
    print("lead random:")
    print(LEAD_RANDOM_ROUGE)


if __name__ == '__main__':
    main()

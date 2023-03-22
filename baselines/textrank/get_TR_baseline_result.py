from nltk import sent_tokenize
from tqdm import tqdm
from rouge_score import rouge_scorer, scoring
import os
import json
import re
import csv
import click
from tqdm import tqdm


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
N_SENT = 2


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
    #lead_rouge = calculate_rouge(["".join(src_sents[:N_SENT])], [tgt])
    lead_output = src_sents[:N_SENT]
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
    #oracle_rouge = calculate_rouge(["".join(output)], [tgt])
    #orig_rouge = calculate_rouge([src], [tgt])
    # print(max_rouge)
    # print(output)
    return output, lead_output


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


@click.command()
@click.option('--data-dir', required=False, type=str, help='Data directory.')
@click.option('--input-file-name', required=False, type=str, help='Input file name.')
@click.option('--lang', required=False, type=str, help='Data directory.')
@click.option('--output-dir', required=False, type=str, help='Output directory.')
def main(data_dir, input_file_name, lang, output_dir):
    srcs = []
    tgts = []
    for line in open(os.path.join(data_dir, input_file_name+".source"), 'r'):
        srcs.append(json.loads(line))
    for line in open(os.path.join(data_dir, input_file_name+".target"), 'r'):
        tgts.append(json.loads(line))

    N = len(srcs)
    SUMMARY = []
    TR_ORACLE_RESULT = []
    TR_LEAD_RESULT = []
    for i in tqdm(range(N)):
        oracle_output, lead_output = greedy_selection(
            srcs[i], tgts[i], N_SENT, lang)
        SUMMARY.append(tgts[i])
        TR_ORACLE_RESULT.append("".join(oracle_output))
        TR_LEAD_RESULT.append("".join(lead_output))

    rouge_lang = lang_to_rouge_lang[lang]
    TR_ORACLE_ROUGE = calculate_rouge(
        TR_ORACLE_RESULT, SUMMARY, rouge_lang)
    TR_LEAD_ROUGE = calculate_rouge(
        TR_LEAD_RESULT, SUMMARY, rouge_lang)

    output_file_tr_oracle = open(os.path.join(
        output_dir, "{}_TR_oracle.jsonl".format(lang)), 'w')
    output_file_lead_oracle = open(os.path.join(
        output_dir, "{}_TR_lead.jsonl".format(lang)), 'w')

    for result in TR_ORACLE_RESULT:
        json.dump(result, output_file_tr_oracle)
        output_file_tr_oracle.write("\n")
    output_file_tr_oracle.close()
    print("TR oracle:")
    print(TR_ORACLE_ROUGE)

    for result in TR_LEAD_RESULT:
        json.dump(result, output_file_lead_oracle)
        output_file_lead_oracle.write("\n")
    output_file_lead_oracle.close()
    print("TR lead:")
    print(TR_LEAD_ROUGE)


if __name__ == '__main__':
    main()

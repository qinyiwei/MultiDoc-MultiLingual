from nltk import sent_tokenize
from tqdm import tqdm
from rouge_score import rouge_scorer, scoring
import os
import json
import re
import csv
import click

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
    return max_rouge["rouge2"]


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
@click.option('--output-dir', required=False, type=str, help='Output directory.')
@click.option('--input-file-name', required=False, type=str, help='Input file name.')
@click.option('--output-file-name', required=False, type=str, help='Output file name.')
def main(data_dir, output_dir, input_file_name, output_file_name):
    start_id = 0
    end_id = None
    lang = input_file_name.split("_")[0]

    if lang == "cantonese" or lang == "chinese":
        LENGTH = 1000
    elif lang == "UA" or lang == "VI":
        LENGTH = 5000
    else:
        LENGTH = 2000

    data = []
    for line in open(os.path.join(data_dir, input_file_name), 'r'):
        data.append(json.loads(line))

    if os.path.exists(os.path.join(output_dir, output_file_name)):
        output_file = open(os.path.join(output_dir, output_file_name), 'r')
        for row in output_file:
            start_id += 1
        output_file.close()

    output_file = open(os.path.join(output_dir, output_file_name), 'a')
    writer = csv.writer(output_file, delimiter='\t')

    num_links = 0
    for i in tqdm(range(start_id, len(data) if end_id is None else end_id)):
        summary = preprocess(data[i]['summary'])

        references_aug = []
        print("--------------------------------num_sum_id_{}-------------------------".format(i))
        print(summary)
        j = 0
        for aug_docs in data[i]['references']:
            j += 1
            print("-------ref_number_{}------".format(j))
            if aug_docs['state'] != 'successful' or len(aug_docs['text']) == 0:
                oracle_socre = None

                print("extraction failed!")
                print(oracle_socre)
            else:
                oracle_socre = greedy_selection(
                    aug_docs['text'][:LENGTH], summary, 2, lang)

                print(aug_docs['text'][:LENGTH])
                print(oracle_socre)

            aug_docs['oracle_socre'] = oracle_socre

        j = 0
        for aug_docs in data[i]['references_aug']:
            j += 1
            print("-------aug_number_{}------".format(j))
            if aug_docs['state'] != 'successful' or len(aug_docs['text']) == 0:
                oracle_socre = None

                print("extraction failed!")
                print(oracle_socre)
            else:
                oracle_socre = greedy_selection(
                    aug_docs['text'][:LENGTH], summary, 2, lang)

                print(aug_docs['text'][:LENGTH])
                print(oracle_socre)

            aug_docs['oracle_socre'] = oracle_socre

        data[i]['summary'] = summary
        json.dump(data[i], output_file)
        output_file.write("\n")


if __name__ == '__main__':
    main()

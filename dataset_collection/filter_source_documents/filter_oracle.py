from tqdm import tqdm
import os
import json
import re
import csv
import click


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


LENGTH = 1000


@click.command()
@click.option('--threshold', required=False, type=float, help='Oracle filter threshold.')
@click.option('--data-dir', required=False, type=str, help='Data directory.')
@click.option('--output-dir', required=False, type=str, help='Output directory.')
@click.option('--input-file-name', required=False, type=str, help='Input file name.')
@click.option('--output-file-name', required=False, type=str, help='Output file name.')
def main(threshold, data_dir, output_dir, input_file_name, output_file_name):
    start_id = 0
    end_id = None

    data = []
    id = 0
    for line in open(os.path.join(data_dir, input_file_name), 'r'):
        id += 1
        try:
            data.append(json.loads(line))
        except:
            print("wrong example:")
            print(id)
            print(line)

    output_file = open(os.path.join(output_dir, output_file_name), 'w')

    num_links_ref = 0
    num_links_aug = 0
    num_links_ref_orig = 0
    num_links_aug_orig = 0
    num_summary = 0
    num_summary_orig = len(data)
    for i in tqdm(range(start_id, len(data) if end_id is None else end_id)):
        summary = preprocess(data[i]['summary'])
        if 'date-range' in data[i]:
            data[i].pop('date-range')
        data[i]['summary'] = summary
        references = []
        references_aug = []
        # print("--------------------------------num_sum_id_{}-------------------------".format(i))
        # print(summary)

        for j in range(len(data[i]['references'])):
            aug_docs = data[i]['references'][j]
            # print("-------ref_number_{}------".format(j))
            if aug_docs['state'] == 'successful' and len(aug_docs['text']) != 0:
                num_links_ref_orig += 1
            if aug_docs['state'] != 'successful' or len(aug_docs['text']) == 0 \
                    or aug_docs['oracle_socre'] is None or aug_docs['oracle_socre'] < threshold:
                continue
            else:
                references.append(aug_docs)
                #print("save this example!")
                # print(aug_docs['oracle_socre'])
                # print(aug_docs['text'][:LENGTH])
            aug_docs.pop('state')
            aug_docs.pop('error')
        data[i]['references'] = references
        num_links_ref += len(data[i]['references'])

        for j in range(len(data[i]['references_aug'])):
            aug_docs = data[i]['references_aug'][j]
            # print("-------aug_number_{}------".format(j))
            if aug_docs['state'] == 'successful' and len(aug_docs['text']) != 0:
                num_links_aug_orig += 1
            if aug_docs['state'] != 'successful' or len(aug_docs['text']) == 0 \
                    or aug_docs['oracle_socre'] is None or aug_docs['oracle_socre'] < threshold:
                continue
            else:
                references_aug.append(aug_docs)
                #print("save this example!")
                # print(aug_docs['oracle_socre'])
                # print(aug_docs['text'][:LENGTH])
            aug_docs.pop('state')
            aug_docs.pop('error')
        data[i]['references_aug'] = references_aug
        num_links_aug += len(data[i]['references_aug'])

        if len(references) == 0 and len(references_aug) == 0:
            continue

        json.dump(data[i], output_file)
        output_file.write("\n")
        num_summary += 1

    print("num_summary:{}, num_ref:{}".format(
        num_summary, num_links_ref+num_links_aug))
    print("num_link_ref:{},avg_num_link_ref:{}".format(
        num_links_ref, num_links_ref/num_summary))
    print("num_links_aug:{},avg_num_link_aug:{}".format(
        num_links_aug, num_links_aug/num_summary))

    print("num_summary_orig:{}, num_ref:{}".format(
        num_summary_orig, num_links_ref_orig+num_links_aug_orig))
    print("num_link_ref_orig:{},avg_num_link_ref_orig:{}".format(
        num_links_ref_orig, num_links_ref_orig/num_summary_orig))
    print("num_links_aug_orig:{},avg_num_link_aug_orig:{}".format(
        num_links_aug_orig, num_links_aug_orig/num_summary_orig))


if __name__ == '__main__':
    main()

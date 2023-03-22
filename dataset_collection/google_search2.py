from googleapiclient.discovery import build
import pprint
import json
import os
from os import link
import re
import csv
import time
import datetime
from googleapiclient.errors import HttpError

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


def google_search(search_term, api_key, cse_id, **kwargs):
    service = build("customsearch", "v1", developerKey=api_key)
    res = service.cse().list(q='{} -filetype:pdf -filetype:txt -filetype:xls -filetype:doc -filetype:docx -filetype:ppt -filetype:pptx -filetype:jsonl'.format(search_term),
                             cx=cse_id, **kwargs).execute()
    if 'items' in res:
        return res['items']
    else:
        print(
            "--------------------------------no items in res-----------------------------")
        return []


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


def process_keywords(orig_text, keywords, lang):
    keys = [i for i in re.findall(r"'.*?'", keywords)]
    filter_words = [key[1:-1] for key in keys]
    text = preprocess(orig_text)
    if len(filter_words) == 0:
        short_text = text
    else:
        short_text = ''
        for w in filter_words:
            short_text += w + ' '
    short_text = short_text.rstrip()
    return short_text


MY_API_KEY =  # add your google search API key
MY_CSE_ID =  # add your Custom Search Engine ID

if __name__ == "__main__":
    data_dir = "./Multi-Doc-Sum/Mtl_data"
    keywords_dir = "./Multi-Doc-Sum/keywords_extraction_keyBERT"
    data_aug_dir = "./Multi-Doc-Sum/Mtl_data_aug_keyBERT"

    file_name = "CZ_crawl_new.jsonl"
    #file_name = "VI_crawl.jsonl"
    #file_name = "RU_crawl_combined.jsonl"
    #file_name = "PL_crawl_combined_new.jsonl"
    #file_name = "UA_crawl.jsonl"

    data = []
    for line in open(os.path.join(data_dir, file_name), 'r'):
        data.append(json.loads(line))

    keywords_dict = {}
    lang = file_name.split("_")[0]
    keywords_file = open(os.path.join(keywords_dir, lang+'_keywords.csv'), 'r')
    csvreader = csv.reader(keywords_file, delimiter='\t')
    for row in csvreader:
        index = int(row[0])
        keys = row[2]
        keywords_dict[index] = keys

    data_aug = []

    start_id = 0
    data_num = None
    data_aug_num = 10
    pages = 2

    id = 0
    output_file_name = os.path.join(
        data_aug_dir, file_name.replace('crawl', 'aug_google'))
    if os.path.exists(output_file_name):
        output_file = open(output_file_name, 'r')
        for row in output_file:
            id += 1
        output_file.close()

    output_file = open(output_file_name, 'a')

    lang = file_name.split("_")[0]
    id = start_id + id

    while id < (len(data) if data_num is None else data_num):
        text = data[id][lang_2_summary_dict[lang]]
        date = data[id]["date"]
        print(date)

        # use date+keywords as Query
        keywords = keywords_dict[id]
        keywords = process_keywords(text, keywords, lang)
        keywords = date + ' ' + keywords

        # use summary as Query
        #keywords = preprocess(text)

        aug_links = []
        page_id = 0

        while (page_id < pages):
            try:
                results = google_search(keywords, MY_API_KEY, MY_CSE_ID,
                                        num=data_aug_num, start=data_aug_num*page_id+1)
                if len(results) != 0:
                    aug_links.extend([result['link'] for result in results])
                page_id += 1
                if len(results) < data_aug_num:
                    break
            except HttpError as e:
                print(f'HttpError, Retrying in 10 seconds...')
                time.sleep(10)
                exit()
                continue
            except Exception as e:
                print(e)
                exit()
        data_cur = {
            "id": id,
            "date": date,
            "query": keywords,
            "summary": text,
            "references_aug": aug_links
        }
        data_aug.append(data_cur)
        print("orig text:{}".format(text))
        print("short text:{}".format(keywords))
        print("data example id {}, num of aug links:{}".format(id, len(aug_links)))
        for link in aug_links:
            print(link)
        print("\n\n")

        json.dump(data_cur, output_file)
        output_file.write("\n")
        id = id + 1
    output_file.close()

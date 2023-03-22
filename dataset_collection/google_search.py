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

PL_month_dict = {
    "Stycznia": 1,
    "stycznia": 1,
    "lutego": 2,
    "marca": 3,
    "kwietnia": 4,
    "maja": 5,
    "czerwca": 6,
    "lipca": 7,
    "sierpnia": 8,
    "września": 9,
    "października": 10,
    "listopada": 11,
    "grudnia": 12,
}

RU_month_dict = {
    "января": 1,
    "февраля": 2,
    "марта": 3,
    "апреля": 4,
    "мая": 5,
    "июня": 6,
    "июля": 7,
    "августа": 8,
    "сентября": 9,
    "октября": 10,
    "ноября": 11,
    "декабря": 12,
}
UA_month_dict = {
    "січня": 1,
    "лютого": 2,
    "березня": 3,
    "квітня": 4,
    "травня": 5,
    "червня": 6,
    "липня": 7,
    "серпня": 8,
    "вересня": 9,
    "жовтня": 10,
    "листопада": 11,
    "грудня": 12,
}
CZ_month_dict = {
    "ledna": 1,
    "února": 2,
    "března": 3,
    "dubna": 4,
    "červejaznce": 4,
    "května": 5,
    "června": 6,
    "července": 7,
    "srpna": 8,
    "září": 9,
    "října": 10,
    "říjen": 10,
    "listopadu": 11,
    "prosince": 12,
    "prosinec": 12,

}


def google_search(search_term, api_key, cse_id, **kwargs):
    service = build("customsearch", "v1", developerKey=api_key)
    #res = service.cse().list(q=search_term, cx=cse_id, **kwargs).execute()
    res = service.cse().list(q='{} -filetype:pdf -filetype:txt -filetype:xls -filetype:doc -filetype:docx -filetype:ppt -filetype:pptx -filetype:jsonl'.format(search_term),
                             cx=cse_id, **kwargs).execute()
    if 'items' in res:
        return res['items']
    else:
        print(
            "--------------------------------no items in res-----------------------------")
        return []


def get_date_range(year=None, month=None, day=None):
    if year is None:
        return None, None
    elif month is None:
        year_s = year
        year_e = year
        month_s = 1
        day_s = 1
        month_e = 12
        day_e = 31
    elif day is None:
        month_s = (month+10) % 12+1
        month_e = (month) % 12+1
        if month_s > month:
            year_s = year-1
        else:
            year_s = year
        if month_e < month:
            year_e = year+1
        else:
            year_e = year
        day_s = 1
        if month_e == 2:
            day_e = 28
        elif month_e in [1, 3, 5, 7, 8, 10, 12]:
            day_e = 31
        else:
            day_e = 30
    else:
        month_s = (month+10) % 12+1
        month_e = (month) % 12+1
        if month_s > month:
            year_s = year-1
        else:
            year_s = year
        if month_e < month:
            year_e = year+1
        else:
            year_e = year
        day_s = day
        day_e = day
        if month_s == 2:
            day_s = min(day_s, 28)
        elif month_s in [1, 3, 5, 7, 8, 10, 12]:
            day_s = min(day_s, 31)
        else:
            day_s = min(day_s, 30)

        if month_e == 2:
            day_e = min(day_e, 28)
        elif month_e in [1, 3, 5, 7, 8, 10, 12]:
            day_e = min(day_e, 31)
        else:
            day_e = min(day_e, 30)

    #start_time = datetime.date(year_s, month_s, day_s)
    #end_time = datetime.date(year_e, month_e, day_e)

    start_time = str(year_s)+str(month_s).rjust(2, '0') + \
        str(day_s).rjust(2, '0')
    end_time = str(year_e)+str(month_e).rjust(2, '0')+str(day_e).rjust(2, '0')

    return start_time, end_time


def parse_date(date_orig, lang):
    try:
        if lang == 'EN':
            date = date_orig.split("-")
            year = int(date[0])
            month = int(date[1])
            day = int(date[2])
        if lang == 'chinese':
            year = int(date_orig.split("年")[0])
            tmp = date_orig.split("年")[1]
            month = int(tmp.split("月")[0])
            tmp = tmp.split("月")[1]
            day = int(tmp.split("日")[0])
        if lang == 'cantonese':
            year = int(date_orig.split("年")[0])
            tmp = date_orig.split("年")[1]
            month = int(tmp.split("月")[0])
            tmp = tmp.split("月")[1]
            day = int(tmp.split("號")[0])
        if lang == 'PL':
            date = date_orig.split(" ")
            if len(date) != 3:
                if len(date) == 2:
                    month = PL_month_dict[date[1]]
                    if "-" in date[0]:
                        day = int(date[0].split("-")[0])
                    elif "–" in date[0]:
                        day = int(date[0].split("–")[0])
                    else:
                        day = int(date[0])
                    return None, month, day
            else:
                year = int(date[2])
                month = PL_month_dict[date[1]]
                day = int(date[0])
        if lang == 'RU':
            date_orig = date_orig.lstrip()
            date = re.split('\s+', date_orig)
            try:
                year = int(date[2])
                month = RU_month_dict[date[1]]
                day = int(date[0])
            except:
                year = int(date[-1])
                return year, None, None
        if lang == 'UA':
            date = date_orig.split(" ")
            if len(date) != 3:
                if (len(date) == 2):
                    year = int(date[1])
                    month = int(date[0])
                    return year, month, None
                if date_orig == "Нобелівської премії миру 2021":
                    year = 2021
                    return year, None, None
            else:
                year = int(date[2])
                month = UA_month_dict[date[1]]
                day = int(date[0])
        if lang == 'CZ':
            if date_orig == "3.2010":
                return 2010, 3, None
            date = re.split('\s+|\xa0', date_orig)

            if len(date) != 3:
                year = int(date_orig[-4:])
                date = date_orig[:-4]
                date = re.split(' |\xa0', date)
                if len(date) == 4 or len(date) == 5:
                    day = int(date[0][:-1])
                    month = CZ_month_dict[date[1]]
                    week = date[3]
                if len(date) == 2:
                    month = CZ_month_dict[date[1]]
                    day = int(date[0][:-1])
                return year, month, day
            else:
                year = int(date[2])
                month = CZ_month_dict[date[1]]
                day = int(date[0][:-1])
        if lang == 'VI':
            return date_orig, date_orig, date_orig
        return year, month, day
    except:
        print("Lang:{}, data_orig:{}, date:{}".format(lang, date_orig, date))
        return None, None, None


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
    file_name = "cantonese_crawl.jsonl"

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
    #YEAR = []
    #MONTH = []
    #DAY  = []
    while id < (len(data) if data_num is None else data_num):
        text = data[id][lang_2_summary_dict[lang]]
        keywords = keywords_dict[id]
        keywords = process_keywords(text, keywords, lang)
        date = data[id]["date"]
        year, month, day = parse_date(date, lang)
        # print(date)
        # YEAR.append(year)
        # MONTH.append(month)
        # DAY.append(month)

        start_date, end_date = get_date_range(year, month, day)
        print("orig date:{}/{}/{}".format(year, month, day))
        print("start_date:{}, end_date:{}".format(start_date, end_date))

        aug_links = []
        page_id = 0

        while (page_id < pages):
            try:
                results = google_search(keywords, MY_API_KEY, MY_CSE_ID,
                                        sort="date:r:{}:{}".format(
                                            start_date, end_date),
                                        num=data_aug_num, start=data_aug_num*page_id+1)
                if len(results) != 0:
                    aug_links.extend([result['link'] for result in results])
                page_id += 1
                if len(results) < data_aug_num:
                    break
            except HttpError as e:
                print(f'HttpError, Retrying in 10 seconds...')
                time.sleep(10)
                continue
            except Exception as e:
                print(e)
                exit()
        data_cur = {
            "id": id,
            "date": date,
            "date-range": "{}-{}".format(start_date, end_date),
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
    # print(list(set(YEAR)))
    # print(list(set(MONTH)))
    # print(list(set(DAY)))
    output_file.close()

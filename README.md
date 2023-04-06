# MultiDoc-MultiLingual


## Dataset Augmentation
We use Google Search Engine to find more input articles for each event from the WCEP with the following steps:
### Extract Keywords
We use keyBERT to extract keywords by running:
```bash
$ python dataset_collection/keywords_extraction_keyBERT.py \
    --file_name "cantonese_crawl.jsonl" \
    --data_dir "./Multi-Doc-Sum/Mtl_data" \
    --output_dir "./Multi-Doc-Sum/keywords_extraction_keyBERT"
```

The meaning of the arguments are as follows:
--data_dir dataset directory of the original crawled data from WCEP.
--file_name a specific file of a certain language under the dataset directory.
--output_dir output directory of the extracted keywords.


### Google Search
We run the following command to search Google:
```bash
$ python dataset_collection/google_search.py \
    --my_api_key $GOOGLE_SEARCH_API_KEY \
    --my_cse_id $CUSTOM_SEARCH_ENGINE_ID \
    --file_name "cantonese_crawl.jsonl" \
    --data_dir "./Multi-Doc-Sum/Mtl_data" \
    --keywords_dir "./Multi-Doc-Sum/keywords_extraction_keyBERT" \
    --data_aug_dir "./Multi-Doc-Sum/Mtl_data_aug_keyBERT" 
```
The meaning of the arguments are as follows:
--MY_API_KEY your google search API key.
--MY_CSE_ID your Custom Search Engine ID.
--data_dir dataset directory of the original crawled data from WCEP.
--file_name a specific file of a certain language under the dataset directory.
--output_dir output directory of the extracted keywords.


## Dataset Cleaning

## Baselines




## Evaluation

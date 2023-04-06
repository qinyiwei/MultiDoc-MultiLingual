from tqdm import tqdm
import os
import json
import click
import random


@click.command()
@click.option('--lang', required=False, type=str, help='language.')
@click.option('--data-dir', required=False, type=str, help='Data directory.')
@click.option('--output-dir', required=False, type=str, help='Output directory.')
@click.option('--input-file-name', required=False, type=str, help='Input file name.')
def main(lang, data_dir, output_dir, input_file_name):
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

    output_file_train = open(os.path.join(
        output_dir, "{}_train.jsonl".format(lang)), 'w')
    output_file_val = open(os.path.join(
        output_dir, "{}_val.jsonl".format(lang)), 'w')
    output_file_test = open(os.path.join(
        output_dir, "{}_test.jsonl".format(lang)), 'w')

    num = len(data)
    ID_shuffle = list(range(0, num))
    random.shuffle(ID_shuffle)

    train_num = int(0.8*num)
    val_num = int(0.1*num)
    train_ID = ID_shuffle[:train_num]
    val_ID = ID_shuffle[train_num:train_num+val_num]
    test_ID = ID_shuffle[train_num+val_num:]

    for i in tqdm(train_ID):
        json.dump(data[i], output_file_train)
        output_file_train.write("\n")
    output_file_train.close()

    for i in tqdm(val_ID):
        json.dump(data[i], output_file_val)
        output_file_val.write("\n")
    output_file_val.close()

    for i in tqdm(test_ID):
        json.dump(data[i], output_file_test)
        output_file_test.write("\n")
    output_file_test.close()


if __name__ == '__main__':
    main()

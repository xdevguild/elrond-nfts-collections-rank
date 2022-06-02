import argparse
import csv
import requests
from operator import itemgetter
from pathlib import Path

# Inputs
parser = argparse.ArgumentParser()
parser.add_argument("--collection", help="Ticker of the collection", required=True)

args = parser.parse_args()
collection_name = args.collection

count = requests.get(f'https://api.elrond.com/collections/{collection_name}/nfts/count').json()

# get all nfts
i = 0
all_nfts = []
attributes_with_count = {}
attributes_with_score = {}

while i < count:
    nfts = requests.get(
        f'https://api.elrond.com/collections/{collection_name}/nfts?from=' + str(i) + '&size=100').json()
    for nft in nfts:
        try:
            # create dict with attributes values count
            for attr in nft['metadata']['attributes']:
                trait_type, value = itemgetter('trait_type', 'value')(attr)
                if attributes_with_count.get(trait_type, None) is not None and attributes_with_count[trait_type].get(
                        value, None) is not None:
                    attributes_with_count[trait_type][value] = attributes_with_count[trait_type][value] + 1
                else:
                    if trait_type not in attributes_with_count:
                        attributes_with_count[trait_type] = {}
                    attributes_with_count[trait_type][value] = 1
            all_nfts.append(nft)
        except:
            pass
    i = i + 100

# calculate attributes score
for trait in attributes_with_count:
    attributes_with_score[trait] = {}
    nfts_with_no_trait = count

    for value in attributes_with_count[trait]:
        trait_count = attributes_with_count[trait][value]
        attributes_with_score[trait][value] = float(1 / trait_count / count)
        nfts_with_no_trait = nfts_with_no_trait - trait_count

    if nfts_with_no_trait != 0:
        attributes_with_score[trait][f'No {trait}'] = float(1 / nfts_with_no_trait / count)

# calculate nft score
for nft in all_nfts:
    for trait in attributes_with_score:
        trait_value = next((a['value'] for a in nft['metadata']['attributes'] if a['trait_type'] == trait), None)
        nft['score'] = nft.get('score', 0) + attributes_with_score[trait][
            f'No {trait}' if trait_value is None else trait_value]

all_nfts.sort(key=lambda x: x.get('score'), reverse=True)

p = Path('output')
p.mkdir(parents=True, exist_ok=True)

# export
with open(f"output/{collection_name}.csv", "wt") as file:
    writer = csv.writer(file, delimiter=",")
    writer.writerow(["Identifier", "Rank"])  # write header
    for idx, output in enumerate(all_nfts, start=1):
        writer.writerow([output['identifier'], idx])

print(f'CSV with rarities successfully exported at ./output/{collection_name}.csv')
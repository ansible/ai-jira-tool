import sys
import csv
import os
import html

print("Current Working Directory:", os.getcwd())

def create_output_filename(input_filename, suffix='_clustered'):
    # Split the input filename into name and extension
    name, ext = os.path.splitext(input_filename)
    # Concatenate name, suffix, and extension to form the output filename
    output_filename = f"{name}{suffix}{ext}"
    return output_filename

linkeage = 'complete'
all_key = "_all"

import argparse

def parse_columns(s):
    return s.split(';') if s else []

# Create the parser
parser = argparse.ArgumentParser(description='Simple usage: \n -f "input_csv.csv" \n Other parameters are optional. Csv file must be separated by semicolon (;).')

# Add the -d (distance threshold) argument
parser.add_argument(
    '-d',
    '--distance_threshold',
    type=float,
    default=0.50,
    help='Distance threshold as a float value. Bigger the number, larger the clusters. Best results are around 0.5'
)

# Add the -c (columns) argument
parser.add_argument(
    '-c',
    '--columns',
    type=parse_columns,
    default=[],
    help=f'Semicolon-separated list of column names. Parameter {all_key} adds all columns from csv file. Summary column is always added and dont have to be specified. Example: -c "Description;Issue Type"'
)

# Add the -f (input file) argument
parser.add_argument(
    '-f',
    '--input_file',
    type=str,
    default='issues.csv',
    help='Name of the csv input file. Output file will be: {input_file}_clustered.csv. Unless output file is specified.'
)

# Add the -fo (output file) argument
parser.add_argument(
    '-fo',
    '--output_file',
    type=str,
    default='',
    help='Name of the csv output file.'
)

parser.add_argument(
    '-s',
    '--sorting',
    type=str,
    default='size',
    help='Possible values: size (sorts from largest), coherence (sorts clusters with items with smallest distances - thus most coherent clusters first). Default is cluster_size.'
)

# Parse the arguments
args = parser.parse_args()

# Access the parsed arguments
distance_threshold = args.distance_threshold
columns = args.columns
input_file = args.input_file
output_file = args.output_file or create_output_filename(input_file)
sorting = args.sorting

columns_tooltip = "(Note that Summary is added as mandatory column)"
if not (all_key in columns):
    columns = ['Summary'] + columns
else:
    columns_tooltip = ''

# Output the results
print('distance_threshold =', distance_threshold)
print(f'columns = {columns}   {columns_tooltip}  ')
print('input_file =', input_file)
print('output_file =', output_file)
print('sorting =', sorting)

print('-----------------------------');
print('Note that csv file must use semicollon(;) separator.')
print('Running app and loading libraries.')
sys.stdout.flush()

if sorting not in ['size', 'coherence']:
    print(f"Error: Sorting parameter must be either 'size' or 'coherence'.")
    sys.exit(1)


from sentence_transformers import SentenceTransformer
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import pairwise_distances
import numpy as np

print('-----------------------------');
sys.stdout.flush()

lines = []
with open(input_file, 'r',  encoding='utf-8') as file:
    reader = csv.reader(file, delimiter=';')
    rows = list(reader)        # Convert to list of rows

    # select first row and let rows array hold the rest
    header = rows[0]

    if all_key in columns:
        columns = []
        for key in header:
            columns.append(key)
    else:
        # check that all columns match the headers
        missing_columns = [col for col in columns if col not in header]
        if missing_columns:
            print(f"Error: The following columns are missing in the CSV header: {', '.join(missing_columns)}")
            sys.exit(1)
        else:
            print("All specified columns are present in the CSV header.")

    rows = rows[1:]
    # Create a mapping from column names to their indices
    header_dict = {col_name: idx for idx, col_name in enumerate(header)}

    for row in rows:
        line = ''
        
        for header_item in header_dict:
            if header_item in columns:
                col_num = header_dict[header_item]
                line += row[col_num] + ';'
        lines.append(line)


print('Computing embeddings. This might take a while.')
print('')
sys.stdout.flush()

# Embedding
model = SentenceTransformer('all-mpnet-base-v2')
embeddings = model.encode(lines)
embeddings = np.array(embeddings)  # Ensure embeddings is a NumPy array

while True:
    clustering_model = AgglomerativeClustering(
            n_clusters=None,
            distance_threshold=distance_threshold,  # Adjust this threshold based on your data
            metric='cosine',              # Use 'cosine' if you prefer cosine distance
            linkage=linkeage,             # 'ward' linkage works well with euclidean distance
        )

    clustering_model.fit(embeddings)
    cluster_assignment = clustering_model.labels_

    # Mapping from cluster ID to list of sentence indices
    cluster_indices = {}
    for sentence_id, cluster_id in enumerate(cluster_assignment):
        cluster_indices.setdefault(cluster_id, []).append(sentence_id)

    # Compute coherence for each cluster
    coherences = {}
    for cluster_id, indices in cluster_indices.items():
        if len(indices) < 2:
            coherence = 0.0  # Coherence is zero if there's only one sentence in the cluster
        else:
            cluster_embeddings = embeddings[indices]
            distances = pairwise_distances(cluster_embeddings, metric='cosine')
            n = distances.shape[0]
            triu_indices = np.triu_indices(n, k=1)
            upper_tri_distances = distances[triu_indices]
            coherence = upper_tri_distances.mean()
        coherences[cluster_id] = coherence

    # Organize sentences by clusters and sort them
    clustered_sentences = {}
    for sentence_id, cluster_id in enumerate(cluster_assignment):
        clustered_sentences.setdefault(cluster_id, []).append(lines[sentence_id])


    # Sort the clusters by size
    if sorting == 'size':
        sorting_set = True
        sorted_clusters = sorted(clustered_sentences.items(), key=lambda item: len(item[1]), reverse=True)
        max_clusters = len(sorted_clusters)

        sorted_cluster_ids = sorted(cluster_indices.keys(), key=lambda cid: len(cluster_indices[cid]), reverse=True)

    if sorting == 'coherence':
        sorted_clusters = sorted(clustered_sentences.items(), key=lambda item: coherences[item[0]])
        max_clusters = len(sorted_clusters)

        sorted_cluster_ids = sorted(cluster_indices.keys(), key=lambda cid: coherences[cid])

    large_clusters_count = 0
    success = False
    while not success:
        try:
            # Open the CSV file for writing
            with open(output_file, 'w', newline='',  encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile, delimiter=';')

                # Write the header
                writer.writerow(header)
                large_clusters_count = 0
                # Write clusters to the CSV file
                for cluster_id in sorted_cluster_ids:
                    indices = cluster_indices[cluster_id]

                    if len(indices) > 1:
                        writer.writerow([ f'Cluster items distance: {coherences[cluster_id]:.4f}'])

                    for idx in indices:
                        if len(indices) > 1:
                            writer.writerow(rows[idx])
                    # Write empty lines to separate clusters
                    if len(indices) > 1:
                        large_clusters_count = large_clusters_count + 1
                        writer.writerow([])
                        writer.writerow([])
                        writer.writerow([])
                        writer.writerow([])

                # write miscelaneous cluster
                writer.writerow([ f'Miscelaneous cluster'])
                for cluster_id in sorted_cluster_ids:
                    indices = cluster_indices[cluster_id]

                    if len(indices) == 1:
                        for idx in indices:
                            writer.writerow(rows[idx])


            success = True  # Writing succeeded, exit the loop
        except Exception as e:
            print(e)
            print("--------------------------------------------------------------------------------------------------------------")
            print(f"Error: Writing to {output_file} threw an exception. Make sure you don't have your file opened and locked for writing. Please resolve the problem and press any key to write the file again.")
            input()

    # now write it into html file
    success = False
    html_output_file = output_file.replace('.csv', '.html')
    while not success:
        try:
            # Open the HTML file for writing
            with open(html_output_file, 'w', encoding='utf-8') as htmlfile:
                # Write the initial HTML structure
                htmlfile.write('<html>\n<head>\n<meta charset="UTF-8">\n<title>Clusters</title>\n')
                htmlfile.write('<style>\n')
                # Add some CSS styles here if needed
                htmlfile.write('table {border-collapse: collapse; width: 100%; }\n')
                htmlfile.write('th, td {border: 1px solid black; padding: 8px; text-align: left;}\n')
                htmlfile.write('.cluster-header {background-color: #f2f2f2; font-weight: bold;}\n')
                htmlfile.write('</style>\n')
                htmlfile.write('</head>\n<body>\n')

                htmlfile.write('<table>\n')

                large_clusters_count = 0

                # Write clusters to the HTML file
                for cluster_id in sorted_cluster_ids:
                    indices = cluster_indices[cluster_id]

                    if len(indices) > 1:
                        # Write the cluster header row
                        htmlfile.write(f'<tr class="cluster-header"><td colspan="{len(header)}">Cluster items distance: {coherences[cluster_id]:.4f}</td></tr>\n')

                        # Write the header row
                        htmlfile.write('<tr>')
                        for col_name in header:
                            htmlfile.write(f'<th>{html.escape(col_name)}</th>')
                        htmlfile.write('</tr>\n')

                        # Write the data rows
                        for idx in indices:
                            htmlfile.write('<tr>')
                            cell_id = -1
                            for cell in rows[idx]:
                                cell_id += 1
                                if header[cell_id] == "Issue key":
                                    htmlfile.write(f'<td><a href="https://issues.redhat.com/browse/{cell}">{html.escape(cell)}</a></td>')
                                else:
                                    htmlfile.write(f'<td>{html.escape(cell)}</td>')
                            htmlfile.write('</tr>\n')

                        # Write empty lines to separate clusters
                        large_clusters_count += 1
                        htmlfile.write(f'<tr><td colspan="{len(header)}">&nbsp;</td></tr>\n' * 2)

                # Write miscellaneous cluster
                htmlfile.write(f'<tr class="cluster-header"><td colspan="{len(header)}">Miscellaneous cluster</td></tr>\n')
                
                # Write the header row
                htmlfile.write('<tr>')
                for col_name in header:
                    htmlfile.write(f'<th>{html.escape(col_name)}</th>')
                htmlfile.write('</tr>\n')
                
                for cluster_id in sorted_cluster_ids:
                    indices = cluster_indices[cluster_id]
                    
                    if len(indices) == 1:
                        for idx in indices:
                            htmlfile.write('<tr>')
                            cell_id = -1
                            for cell in rows[idx]:
                                cell_id += 1
                                if header[cell_id] == "Issue key":
                                    htmlfile.write(f'<td><a href="https://issues.redhat.com/browse/{cell}">{html.escape(cell)}</a></td>')
                                else:
                                    htmlfile.write(f'<td>{html.escape(cell)}</td>')
                            htmlfile.write('</tr>\n')

                # Close the table and HTML tags
                htmlfile.write('</table>\n</body>\n</html>\n')

                success = True  # Writing succeeded, exit the loop
        except Exception as e:
            print("--------------------------------------------------------------------------------------------------------------")
            print(f"Error: Writing to {html_output_file} threw an exception. Make sure you don't have your file opened and locked for writing. Please resolve the problem and press any key to write the file again.")
            input()



    print('-------------------------------')
    print(f'Results written to {output_file} and {html_output_file}')
    print(f'Total number of clusters (including single item clusters) {len(sorted_cluster_ids)}')
    print(f'Number of clusters (excluding single item clusters): {large_clusters_count}')
    print()
    print('Results are delimited by several empty lines. Last cluster is miscelaneous cluster - anything that does not belong to any cluster is mixed here.')
    print()
    str = input(f"Enter new cluster distance threshold. Last was {distance_threshold}. The higher the parameter, larger clusters will emerge. Output file will be overwriten by new results (q for quit): ")
    if str == 'q':
        exit(0)
    distance_threshold = float(str)
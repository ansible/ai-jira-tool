import csv
import logging
from io import StringIO
from flask import Flask, request, render_template
from sentence_transformers import SentenceTransformer
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import pairwise_distances
import numpy as np

app = Flask(__name__, template_folder='.')
logger = logging.getLogger(__name__)

# In-memory store for uploaded CSV data
# Key: filename
# Value: {
#     "column_names": [col1, col2, ...],
#     "data": [  # list of rows
#         {col1: val1, col2: val2, ...},
#         ...
#     ]
# }
files_data = {}

@app.route('/api/files', methods=['GET'])
def get_files():
    return {
      'files': files_data
    }

@app.route('/api/table', methods=['GET'])
def get_table():
    index();
    return {
      'column_names': column_names,
      #'data': selected_data
    }

@app.route('/api/upload', methods=['POST'])
def post_upload():
    file = request.files.get("file")
    file_contents = file.read().decode("utf-8", errors="replace")
    csv_reader = csv.reader(StringIO(file_contents), delimiter=';')
    rows = list(csv_reader)
    if len(rows) > 0:
                    # First row is the column names
                    column_names = rows[0]
                    data = []

                    # Build a list of dicts for each subsequent row
                    for row in rows[1:]:
                        row_dict = {}
                        for col_name, cell_value in zip(column_names, row):
                            row_dict[col_name] = cell_value
                        data.append(row_dict)

                    # Store in dictionary
                    files_data[file.filename] = {
                        "column_names": column_names,
                        "data": data
                    }
    return {'file': files_data[file.filename]}


@app.route("/", methods=["GET", "POST"])
def index():
    global files_data, column_names, data

    # Handle file upload if it's a POST request
    if request.method == "POST":
        uploaded_file = request.files.get("csv_file")
        if uploaded_file:
            file_contents = uploaded_file.read().decode("utf-8", errors="replace")

            # Parse the CSV using ';' as delimiter
            csv_reader = csv.reader(StringIO(file_contents), delimiter=';')
            rows = list(csv_reader)

            if len(rows) > 0:
                # First row is the column names
                column_names = rows[0]
                data = []

                # Build a list of dicts for each subsequent row
                for row in rows[1:]:
                    row_dict = {}
                    for col_name, cell_value in zip(column_names, row):
                        row_dict[col_name] = cell_value
                    data.append(row_dict)

                # Store in dictionary
                files_data[uploaded_file.filename] = {
                    "column_names": column_names,
                    "data": data
                }

    # Check if the user wants to view a specific file
    selected_file = request.args.get("file")
    selected_data = None
    column_names = None

    if selected_file and selected_file in files_data:
        column_names = files_data[selected_file]["column_names"]
        selected_data = files_data[selected_file]["data"]

    return render_template(
        "layout.html",
        files=list(files_data.keys()),
        selected_file=selected_file,
        data=selected_data,
        column_names=column_names
    )
# 150 embeding
@app.route('/api/clustering', methods=['POST'])
def post_clustering():
    # summary column + thdreashold input (float 0.2-0.7)
    all_key = "_all"
    columns = ['Summary']
    sorting = 'coherence'

    file = request.files.get("file")
    file_contents = file.read().decode("utf-8", errors="replace")
    csv_reader = csv.reader(StringIO(file_contents), delimiter=';')
    rows = list(csv_reader)

    lines = []
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
          if len(row) > 0:
            line = ''
            print('row =', row)

            for header_item in header_dict:
                print('header_item =', header_item)
                if header_item in columns:
                  col_num = header_dict[header_item]
                  print('col_num =', col_num)
                  print('line =', line)
                  line += row[col_num] + ';'
            lines.append(line)
    model = SentenceTransformer('all-mpnet-base-v2')
    embeddings = model.encode(lines)
    embeddings = np.array(embeddings)


    clustering_model = AgglomerativeClustering(
                n_clusters=None,
                distance_threshold=0.2,       # TODO Adjust this threshold based on your data
                metric='cosine',              # Use 'cosine' if you prefer cosine distance
                linkage='complete',               # 'ward' linkage works well with euclidean distance
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
    print('sorted_clusters =', sorted_clusters)

    success = False
    filename = 'temps'
    file
    while not success:
        try:
            # Open the CSV file for writing
            with open(filename, 'w', newline='',  encoding='utf-8') as csvfile:
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

            print('csv: ', csvfile)
            success = True  # Writing succeeded, exit the loop
        except Exception as e:
            print(e)
            print("--------------------------------------------------------------------------------------------------------------")
            print(f"Error: Writing to {'temp'} threw an exception. Make sure you don't have your file opened and locked for writing. Please resolve the problem and press any key to write the file again.")
            input()
    #file = open(filename, 'r')

    return {'sorted_clusters': open(filename, 'r')}

if __name__ == "__main__":
    app.run(debug=True, port=4400)


import sys
import csv
import os
import html
import argparse
import numpy as np

from sentence_transformers import SentenceTransformer
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import pairwise_distances

# ------------------------------
# Global variables for web mode
# ------------------------------
global_csv_data = None   # Stores CSV data: keys: 'header', 'rows', 'lines'
global_embeddings = None # Cached embeddings as a NumPy array
global_uploaded_file_name = None  # New global variable to store the uploaded file name

# ------------------------------
# Flask App for Web Interface
# ------------------------------
from flask import Flask, request, render_template_string

app = Flask(__name__)
app.config['SECRET_KEY'] = 'replace-this-with-a-secret-key'

# HTML template for the web interface.
template = """
<html>
<head>
    <meta charset="UTF-8">
    <title>{% if uploaded_file_name %}Uploaded file ({{ uploaded_file_name }}){% else %}CSV Clustering App{% endif %}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
        th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
        .cluster-separator { background-color: #f2f2f2; font-weight: bold; }
        .message { padding: 10px; margin-bottom: 20px; border: 1px solid #aaa; background-color: #eee; }
    </style>
</head>
<body>
   {% if message %}
      <div class="message">{{ message }}</div>
    {% endif %}
    <form method="POST" action="/" enctype="multipart/form-data">
         <fieldset>
           <legend>Step 1: Upload CSV File</legend>
           <label for="csv_file">Select CSV file (semicolon-separated):</label>
           <input type="file" name="csv_file" id="csv_file" accept=".csv">
           <input type="submit" name="action" value="Upload CSV">
         </fieldset>
         <br>
         <fieldset>
           <legend>Step 2: Cluster Options</legend>
           <label for="distance_threshold">Cluster distance threshold:</label>
           <input type="text" name="distance_threshold" id="distance_threshold" value="{{ distance_threshold }}">
           <label for="sorting">Sort clusters by:</label>
           <select name="sorting" id="sorting">
               <option value="size" {% if sorting == 'size' %}selected{% endif %}>Group Size</option>
               <option value="coherence" {% if sorting == 'coherence' %}selected{% endif %}>Coherence</option>
           </select>
           <input type="submit" name="action" value="Cluster"> 
           This may take while for larger files, around one minute
         </fieldset>
    </form>
    <hr>
    {% if header %}
      <h2>Clustering Results ( {{ uploaded_file_name }} ) </h2>
      <table>
        <tbody>
          {% if clusters %}
            {% for cluster in clusters %}
            <thead>
                <tr>
                    {% for col in header %}
                    <th>{{ col }}</th>
                    {% endfor %}
                </tr>
            </thead>
              <tr class="cluster-separator">
                <td colspan="{{ header|length }}">Cluster items distance: {{ "%.4f"|format(cluster.coherence) }}</td>
              </tr>
              {% for row in cluster.rows %}
                <tr>
                  {% for cell in row %}
                    {% if header[loop.index0] == "Issue key" %}
                      <td><a href="https://issues.redhat.com/browse/{{ cell }}">{{ cell }}</a></td>
                    {% else %}
                      <td>{{ cell }}</td>
                    {% endif %}
                  {% endfor %}
                </tr>
              {% endfor %}
              <tr><td colspan="{{ header|length }}">&nbsp;</td></tr>
            {% endfor %}
          {% endif %}
          {% if misc %}
            <tr class="cluster-separator">
              <td colspan="{{ header|length }}">Miscellaneous cluster</td>
            </tr>
            {% for row in misc %}
              <tr>
                {% for cell in row %}
                  {% if header[loop.index0] == "Issue key" %}
                    <td><a href="https://issues.redhat.com/browse/{{ cell }}">{{ cell }}</a></td>
                  {% else %}
                    <td>{{ cell }}</td>
                  {% endif %}
                {% endfor %}
              </tr>
            {% endfor %}
          {% endif %}
        </tbody>
      </table>
    {% endif %}
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    global global_csv_data, global_embeddings, global_uploaded_file_name
    message = None
    clusters = None
    misc = None
    header = None

    # Retrieve current settings from the form or use defaults.
    current_distance_threshold = request.form.get("distance_threshold", "0.5")
    current_sorting = request.form.get("sorting", "size")

    if request.method == "POST":
        action = request.form.get("action")
        # --- Handle CSV upload ---
        if action == "Upload CSV":
            file = request.files.get("csv_file")
            if file and file.filename.lower().endswith(".csv"):
                try:
                    content = file.stream.read().decode("utf-8").splitlines()
                    reader = csv.reader(content, delimiter=";")
                    rows_list = list(reader)
                    if not rows_list:
                        message = "CSV file is empty."
                    else:
                        header = rows_list[0]
                        rows = rows_list[1:]
                        lines = [";".join(row) for row in rows]
                        global_csv_data = {"header": header, "rows": rows, "lines": lines}
                        global_embeddings = None  # Reset embeddings when a new file is uploaded
                        global_uploaded_file_name = file.filename  # Store the uploaded file name
                        message = "CSV file uploaded successfully."
                except Exception as e:
                    message = f"Error processing CSV file: {e}"
            else:
                message = "Please upload a valid CSV file."
        # --- Handle clustering ---
        elif action == "Cluster":
            try:
                distance_threshold = float(current_distance_threshold)
            except ValueError:
                message = "Invalid cluster distance threshold."
                return render_template_string(template,
                                              message=message,
                                              header=None,
                                              distance_threshold=current_distance_threshold,
                                              sorting=current_sorting,
                                              uploaded_file_name=global_uploaded_file_name)
            sorting = current_sorting
            if not global_csv_data:
                message = "Please upload a CSV file first."
            else:
                header = global_csv_data["header"]
                if global_embeddings is None:
                    try:
                        model = SentenceTransformer('all-mpnet-base-v2')
                        emb = model.encode(global_csv_data["lines"])
                        global_embeddings = np.array(emb)
                    except Exception as e:
                        message = f"Error computing embeddings: {e}"
                        return render_template_string(template,
                                                      message=message,
                                                      header=header,
                                                      distance_threshold=current_distance_threshold,
                                                      sorting=current_sorting,
                                                      uploaded_file_name=global_uploaded_file_name)
                try:
                    clustering_model = AgglomerativeClustering(
                        n_clusters=None,
                        distance_threshold=distance_threshold,
                        metric='cosine',
                        linkage='complete'
                    )
                    clustering_model.fit(global_embeddings)
                    labels = clustering_model.labels_
                except Exception as e:
                    message = f"Error during clustering: {e}"
                    return render_template_string(template,
                                                  message=message,
                                                  header=header,
                                                  distance_threshold=current_distance_threshold,
                                                  sorting=current_sorting,
                                                  uploaded_file_name=global_uploaded_file_name)
                # Build mapping: cluster id -> row indices.
                cluster_indices = {}
                for idx, label in enumerate(labels):
                    cluster_indices.setdefault(label, []).append(idx)
                # Compute cluster coherence.
                coherences = {}
                for cid, indices in cluster_indices.items():
                    if len(indices) < 2:
                        coherence = 0.0
                    else:
                        cluster_embeds = global_embeddings[indices]
                        distances = pairwise_distances(cluster_embeds, metric='cosine')
                        n = distances.shape[0]
                        triu_indices = np.triu_indices(n, k=1)
                        upper_tri = distances[triu_indices]
                        coherence = upper_tri.mean()
                    coherences[cid] = coherence
                # Sort clusters per chosen method.
                if sorting == "size":
                    sorted_cluster_ids = sorted(cluster_indices.keys(), key=lambda cid: len(cluster_indices[cid]), reverse=True)
                elif sorting == "coherence":
                    sorted_cluster_ids = sorted(cluster_indices.keys(), key=lambda cid: coherences[cid])
                else:
                    sorted_cluster_ids = list(cluster_indices.keys())
                # Separate clusters: multi-item clusters and miscellaneous (singleton) items.
                clusters = []
                misc = []
                for cid in sorted_cluster_ids:
                    indices = cluster_indices[cid]
                    if len(indices) > 1:
                        cluster_rows = [global_csv_data["rows"][i] for i in indices]
                        clusters.append({"coherence": coherences[cid], "rows": cluster_rows})
                    else:
                        misc.extend([global_csv_data["rows"][i] for i in indices])
                message = f"Clustering complete. Found {len(clusters)} clusters and {len(misc)} miscellaneous items."
    return render_template_string(template,
                                  message=message,
                                  clusters=clusters,
                                  misc=misc,
                                  header=header,
                                  distance_threshold=current_distance_threshold,
                                  sorting=current_sorting,
                                  uploaded_file_name=global_uploaded_file_name)

# ------------------------------
# CLI Version (for CLI mode)
# ------------------------------
def run_cli_with_args(args):
    all_key = "_all"
    linkage = 'complete'
    
    def create_output_filename(input_filename, suffix='_clustered'):
        name, ext = os.path.splitext(input_filename)
        output_filename = f"{name}{suffix}{ext}"
        return output_filename

    # Process CLI arguments passed from the top-level parser.
    distance_threshold = args.distance_threshold
    columns = args.columns.split(';') if args.columns is not None else []
    input_file = args.input_file
    output_file = args.output_file if args.output_file else create_output_filename(input_file)
    sorting = args.sorting

    columns_tooltip = "(Note that Summary is always added)"
    if all_key not in columns:
        columns = ['Summary'] + columns
    else:
        columns_tooltip = ''

    print('distance_threshold =', distance_threshold)
    print(f'columns = {columns}   {columns_tooltip}')
    print('input_file =', input_file)
    print('output_file =', output_file)
    print('sorting =', sorting)
    print('-----------------------------')
    print('Note: CSV file must use semicolon (;) as a separator.')
    print('Loading CSV file and libraries...')
    sys.stdout.flush()

    if sorting not in ['size', 'coherence']:
        print("Error: Sorting parameter must be either 'size' or 'coherence'.")
        sys.exit(1)

    lines = []
    with open(input_file, 'r', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter=';')
        rows = list(reader)
        header = rows[0]
        if all_key in columns:
            columns = header
        else:
            missing_columns = [col for col in columns if col not in header]
            if missing_columns:
                print(f"Error: The following columns are missing in the CSV header: {', '.join(missing_columns)}")
                sys.exit(1)
            else:
                print("All specified columns are present in the CSV header.")
        rows = rows[1:]
        header_dict = {col_name: idx for idx, col_name in enumerate(header)}
        for row in rows:
            line = ''
            for header_item in header_dict:
                if header_item in columns:
                    col_num = header_dict[header_item]
                    line += row[col_num] + ';'
            lines.append(line)
    print('Computing embeddings. This might take a while...')
    sys.stdout.flush()

    model = SentenceTransformer('all-mpnet-base-v2')
    embeddings = model.encode(lines)
    embeddings = np.array(embeddings)

    clustering_model = AgglomerativeClustering(
            n_clusters=None,
            distance_threshold=distance_threshold,
            metric='cosine',
            linkage=linkage,
        )
    clustering_model.fit(embeddings)
    cluster_assignment = clustering_model.labels_

    cluster_indices = {}
    for sentence_id, cluster_id in enumerate(cluster_assignment):
        cluster_indices.setdefault(cluster_id, []).append(sentence_id)

    coherences = {}
    for cluster_id, indices in cluster_indices.items():
        if len(indices) < 2:
            coherence = 0.0
        else:
            cluster_embeddings = embeddings[indices]
            distances = pairwise_distances(cluster_embeddings, metric='cosine')
            n = distances.shape[0]
            triu_indices = np.triu_indices(n, k=1)
            upper_tri = distances[triu_indices]
            coherence = upper_tri.mean()
        coherences[cluster_id] = coherence

    if sorting == 'size':
        sorted_cluster_ids = sorted(cluster_indices.keys(), key=lambda cid: len(cluster_indices[cid]), reverse=True)
    elif sorting == 'coherence':
        sorted_cluster_ids = sorted(cluster_indices.keys(), key=lambda cid: coherences[cid])
    else:
        sorted_cluster_ids = list(cluster_indices.keys())

    success = False
    while not success:
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile, delimiter=';')
                writer.writerow(header)
                for cluster_id in sorted_cluster_ids:
                    indices = cluster_indices[cluster_id]
                    if len(indices) > 1:
                        writer.writerow([f'Cluster items distance: {coherences[cluster_id]:.4f}'])
                    for idx in indices:
                        if len(indices) > 1:
                            writer.writerow(rows[idx])
                    if len(indices) > 1:
                        writer.writerow([])
                        writer.writerow([])
                        writer.writerow([])
                        writer.writerow([])
                writer.writerow(['Miscelaneous cluster'])
                for cluster_id in sorted_cluster_ids:
                    indices = cluster_indices[cluster_id]
                    if len(indices) == 1:
                        for idx in indices:
                            writer.writerow(rows[idx])
            success = True
        except Exception as e:
            print(e)
            print("Error writing to output file. Please close it if open and try again.")
            input("Press Enter to retry...")

    html_output_file = output_file.replace('.csv', '.html')
    success = False
    while not success:
        try:
            with open(html_output_file, 'w', encoding='utf-8') as htmlfile:
                htmlfile.write('<html>\n<head>\n<meta charset="UTF-8">\n<title>Clusters</title>\n')
                htmlfile.write('<style>\n')
                htmlfile.write('table {border-collapse: collapse; width: 100%; }\n')
                htmlfile.write('th, td {border: 1px solid black; padding: 8px; text-align: left;}\n')
                htmlfile.write('.cluster-separator {background-color: #f2f2f2; font-weight: bold;}\n')
                htmlfile.write('</style>\n</head>\n<body>\n')
                htmlfile.write('<table>\n<thead>\n<tr>' + ''.join(f'<th>{html.escape(col)}</th>' for col in header) + '</tr>\n</thead>\n<tbody>\n')
                for cluster_id in sorted_cluster_ids:
                    indices = cluster_indices[cluster_id]
                    if len(indices) > 1:
                        htmlfile.write(f'<tr class="cluster-separator"><td colspan="{len(header)}">Cluster items distance: {coherences[cluster_id]:.4f}</td></tr>\n')
                        for idx in indices:
                            htmlfile.write('<tr>')
                            for cell_id, cell in enumerate(rows[idx]):
                                if header[cell_id] == "Issue key":
                                    htmlfile.write(f'<td><a href="https://issues.redhat.com/browse/{cell}">{html.escape(cell)}</a></td>')
                                else:
                                    htmlfile.write(f'<td>{html.escape(cell)}</td>')
                            htmlfile.write('</tr>\n')
                        htmlfile.write(f'<tr><td colspan="{len(header)}">&nbsp;</td></tr>\n')
                htmlfile.write(f'<tr class="cluster-separator"><td colspan="{len(header)}">Miscellaneous cluster</td></tr>\n')
                for cluster_id in sorted_cluster_ids:
                    indices = cluster_indices[cluster_id]
                    if len(indices) == 1:
                        for idx in indices:
                            htmlfile.write('<tr>')
                            for cell_id, cell in enumerate(rows[idx]):
                                if header[cell_id] == "Issue key":
                                    htmlfile.write(f'<td><a href="https://issues.redhat.com/browse/{cell}">{html.escape(cell)}</a></td>')
                                else:
                                    htmlfile.write(f'<td>{html.escape(cell)}</td>')
                            htmlfile.write('</tr>\n')
                htmlfile.write('</tbody>\n</table>\n</body>\n</html>\n')
            success = True
        except Exception as e:
            print("Error writing HTML file. Please close it if open and try again.")
            input("Press Enter to retry...")
    print('-------------------------------')
    print(f'Results written to {output_file} and {html_output_file}')
    print(f'Total number of clusters (including single item clusters): {len(sorted_cluster_ids)}')
    large_clusters_count = sum(1 for cid in sorted_cluster_ids if len(cluster_indices[cid]) > 1)
    print(f'Number of clusters (excluding single item clusters): {large_clusters_count}')
    print('Results are delimited by empty rows; the last cluster is miscellaneous.')
    input("Press Enter to exit.")

# ------------------------------
# Main entry point
# ------------------------------
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="CSV Clustering App. Use --serve <port> to start the Flask web server. "
                    "If --serve is not provided, the following CLI parameters are used for CSV clustering."
    )
    # Web mode parameter.
    parser.add_argument('--serve', type=int,
                        help='(Web mode) Port number on which to run the Flask web server')
    # CLI mode parameters.
    parser.add_argument('-d', '--distance_threshold', type=float, default=0.50,
                        help='(CLI) Distance threshold as a float value. Larger values yield larger clusters. Default is 0.50.')
    parser.add_argument('-c', '--columns', type=str,
                        help='(CLI) Semicolon-separated list of column names. Use "_all" to add all columns. Note: "Summary" is always added.')
    parser.add_argument('-f', '--input_file', type=str, default='issues.csv',
                        help='(CLI) Name of the CSV input file. Default is "issues.csv". CSV must be semicolon-separated.')
    parser.add_argument('-fo', '--output_file', type=str, default='',
                        help='(CLI) Name of the CSV output file. If not specified, the output file will be {input_file}_clustered.csv.')
    parser.add_argument('-s', '--sorting', type=str, default='size', choices=['size', 'coherence'],
                        help="(CLI) Sorting method: 'size' for largest clusters first or 'coherence' for most coherent clusters first. Default is 'size'.")
    args = parser.parse_args()

    if args.serve is not None:
        app.run(host='0.0.0.0', port=args.serve, debug=True)
    else:
        run_cli_with_args(args)

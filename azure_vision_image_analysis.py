import os
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential

# Função para rotular a imagem com base no modelo denseCaptionsResult
def label_dense_captions(json_data, ax):
    for item in json_data["denseCaptionsResult"]["values"]:
        x, y, w, h = item["boundingBox"]["x"], item["boundingBox"]["y"], item["boundingBox"]["w"], item["boundingBox"]["h"]
        ax.add_patch(Rectangle((x, y), w, h, linewidth=2, edgecolor='g', facecolor='none'))
        ax.text(x, y - 10, item["text"], bbox=dict(facecolor='g', alpha=0.5))

# Função para rotular a imagem com base no modelo peopleResult
def label_people(json_data, ax):
    for item in json_data["peopleResult"]["values"]:
        x, y, w, h = item["boundingBox"]["x"], item["boundingBox"]["y"], item["boundingBox"]["w"], item["boundingBox"]["h"]
        ax.add_patch(Rectangle((x, y), w, h, linewidth=2, edgecolor='y', facecolor='none'))
        ax.text(x, y - 10, "Pessoa", bbox=dict(facecolor='y', alpha=0.5))

# Função para rotular a imagem com base no modelo readResult
def label_read_result(json_data, ax):
    for item in json_data["readResult"]["blocks"]:
        for line in item["lines"]:
            for word in line["words"]:
                bounding_polygon = word["boundingPolygon"]
                points = np.array([[point["x"], point["y"]] for point in bounding_polygon])
                ax.add_patch(Polygon(points, closed=True, fill=False, edgecolor='b'))
                ax.text(points[0, 0], points[0, 1] - 10, word["text"], color='b')

# Função para rotular e identificar elementos  na imagem com base no JSON após processamento
def label_image(json_data, ax):
    if "denseCaptionsResult" in json_data:
        label_dense_captions(json_data, ax)
    elif "peopleResult" in json_data:
        label_people(json_data, ax)
    elif "readResult" in json_data:
        label_read_result(json_data, ax)

    ax.set_axis_off()
    return ax

def process_images_in_folder(input_folder, output_folder, endpoint, key):
    # Cria o cliente Vision
    client = ImageAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(key))

    # Mapeamento de prefixo para funcionalidades visuais
    features_map = {
        "analysis": [VisualFeatures.DENSE_CAPTIONS],
        "ocr": [VisualFeatures.READ],
        "people": [VisualFeatures.PEOPLE]
    }

    # Processa cada imagem na pasta de entrada
    for filename in os.listdir(input_folder):
        if filename.lower().endswith((".jpg", ".jpeg", ".png")):
            input_image_path = os.path.join(input_folder, filename)
            output_image_path = os.path.join(output_folder, filename)
            output_json_path = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}.json")
            with open(input_image_path, "rb") as image_file:
                image_data = image_file.read()

            # Determina quais funcionalidades visuais analisar com base no prefixo do nome do arquivo
            prefix = next((key for key in features_map.keys() if filename.startswith(key)), None)
            features = features_map.get(prefix, [])

            # Realiza a análise
            if features:
                result = client.analyze(image_data=image_data, visual_features=features)
                # Salva o resultado como JSON
                with open(output_json_path, "w") as json_file:
                    json.dump(result.as_dict(), json_file, indent=4)

                # Carregar a imagem usando Matplotlib
                image = plt.imread(input_image_path)
                fig, ax = plt.subplots()
                ax.imshow(image)

                # Rotular a imagem com base no modelo no JSON
                with open(output_json_path, "r") as json_file:
                    json_data = json.load(json_file)
                label_image(json_data, ax)

                # Salvar uma segunda versão da imagem na pasta de saída
                plt.savefig(output_image_path, bbox_inches='tight', pad_inches=0)
                plt.close()

if __name__ == "__main__":
    input_folder = "inputs"
    output_folder = "output"
    endpoint = os.environ.get("VISION_ENDPOINT")
    key = os.environ.get("VISION_KEY")
    if not (endpoint and key):
        print("Please set environment variables 'VISION_ENDPOINT' and 'VISION_KEY'.")
    else:
        process_images_in_folder(input_folder, output_folder, endpoint, key)
        print("Processamento concluído.")

import os
import json
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential

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
            
if __name__ == "__main__":
    input_folder = "inputs"
    output_folder = "output"
    endpoint = os.environ.get("VISION_ENDPOINT")
    key = os.environ.get("VISION_KEY")
    if not (endpoint and key):
        print("Please set environment variables 'VISION_ENDPOINT' and 'VISION_KEY'.")
    else:
        process_images_in_folder(input_folder, output_folder, endpoint, key)

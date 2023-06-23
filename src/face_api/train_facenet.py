import os
import cv2 as cv
import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import SVC
import pickle
import logging

logging.basicConfig(filename='app.log', filemode='w',
                    format='%(name)s %(asctime)s - %(levelname)s - %(message)s')

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'


class FaceLoading:
    def __init__(self, directory):
        self.directory = directory
        self.target_size = (160, 160)
        self.X = []
        self.Y = []

    def extract_face(self, filename):
        try:
            logging.info(f"FaceLoading.extract_face({filename}) start")
            img = cv.imread(filename, 0)
            img = cv.cvtColor(img, cv.COLOR_BGR2RGB)
            face_arr = cv.resize(img, self.target_size)
            logging.info(f"FaceLoading.extract_face({filename}) OK")
            return face_arr
        except Exception as e:
            logging.exception(
                f"FaceLoading.extract_face({filename}) exception[{e}]")
            raise Exception(f"Failed to extract_face {e}")
        finally:
            logging.info(f"FaceLoading.load_faces({filename}) finish")

    def load_faces(self, dir):
        try:
            logging.info(f"FaceLoading.load_faces({dir}) start")
            faces = []
            for im_name in os.listdir(dir):
                path = os.path.join(dir, im_name)
                if os.path.exists(path):
                    single_face = self.extract_face(path)
                    faces.append(single_face)
            return faces
        except Exception as e:
            logging.exception(f"FaceLoading.load_faces({dir}) exception[{e}]")
            raise Exception(f"Failed to load faces {e}")
        finally:
            logging.info(f"FaceLoading.load_faces({dir}) finish")

    def load_classes(self):
        try:
            logging.info(f"FaceLoading.load_classes() start")
            for sub_dir in os.listdir(self.directory):
                path = os.path.join(self.directory, sub_dir)
                faces = self.load_faces(path)
                labels = [sub_dir for _ in range(len(faces))]
                print(f"Loaded successfully Id({sub_dir}): {len(labels)}")
                self.X.extend(faces)
                self.Y.extend(labels)
            return np.asarray(self.X), np.asarray(self.Y)
        except Exception as e:
            logging.exception(f"FaceLoading.load_faces({dir}) exception[{e}]")
            raise Exception(f"Failed to load classes {e}")
        finally:
            logging.info(f"FaceLoading.load_classes() finish")


def train_facenet(embedder, encoder, path_dataset, path_embedding, path_model):
    try:
        logging.info(
            f"train_facenet start path_dataset[{path_dataset}] path_embedding[{path_embedding}] path_model[{path_model}]")
        print(f"train_facenet start")
        face_loading = FaceLoading(path_dataset)
        X, Y = face_loading.load_classes()

        # embedder = FaceNet()
        embedded_X = []

        for img in X:
            embedded_X.append(embedder.embeddings(
                np.expand_dims(img.astype('float32'), axis=0))[0])
        embedded_X = np.asarray(embedded_X)

        # Save the face embeddings and their corresponding labels to a compressed numpy file
        np.savez_compressed(path_embedding, embedded_X, Y)

        # # Encode labels using LabelEncoder and split the data into train and test sets
        # encoder = LabelEncoder()
        encoder.fit(Y)
        Y_encoded = encoder.transform(Y)

        # Train a linear SVM model
        model = SVC(kernel='linear', probability=True)
        model.fit(embedded_X, Y_encoded)

        # Save the trained model to a pickle file
        with open(path_model, 'wb') as f:
            pickle.dump(model, f)
        logging.info(f"train_facenet OK")
    except Exception as ex:
        logging.exception(f"train_facenet failed, exception[{ex}]")
        raise Exception(f"Failed to train model {ex}")
    finally:
        print(f"train_facenet finish")
        logging.info(f"train_facenet finish")

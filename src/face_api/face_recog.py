import cv2
import numpy as np
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import tensorflow as tf
from sklearn.preprocessing import LabelEncoder
import pickle
from keras_facenet import FaceNet
# import time

def avg(x, idx):
    sum = 0
    for i in x:
        if i != x[idx]:
            sum += i
    return float(sum/(len(x)-1))
def compare(a, b):
    div =1 - float(b/a) * 100
    # print(div)
    return (div >= 0.6)

def get_ID(facenet, encoder, path_embedding, path_model, image):
    # Initialize FaceNet
    # facenet = FaceNet()

    # Load precomputed face embeddings
    faces_embeddings = np.load(path_embedding)
    X = faces_embeddings['arr_0']
    Y = faces_embeddings['arr_1']

    # Encode labels using sklearn's LabelEncoder
    # encoder = LabelEncoder()
    encoder.fit(Y)

    # Load SVM model for face recognition
    model = pickle.load(open(path_model, 'rb'))

    # Convert frame to RGB and grayscale
    rgb_img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    img = cv2.resize(rgb_img, (160, 160))

    # Compute face embedding using FaceNet
    img = np.expand_dims(img, axis=0)
    ypred = facenet.embeddings(img)

    # Recognize face using SVM model
    yhat_class = model.predict(ypred)
    yhat_prob = model.predict_proba(ypred) # lưu xác xuất dự đoán

    # get name
    class_index = yhat_class[0]
    class_probability = yhat_prob[0,class_index] * 100
    predict_names = encoder.inverse_transform(yhat_class)
    name = predict_names[0]
    average_prob = avg(yhat_prob[0], class_index)
    if compare(class_probability, average_prob) == False:
        name = "-1"

    return int(name)        




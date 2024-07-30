# Alzheimer-s-Disease-Classification

# Abstract 

Alzheimer's disease is a neurological disease that often affects older adults and is 
characterized by progressive cognitive decline. It is the most common cause of 
dementia, a syndrome that impairs memory, thinking, and behaviour. However, to 
diagnose stages of Alzheimer’s disease, it depends solely on the medical profession,
and it is a time-consuming process as numbers of brain segmentation is needed to 
diagnose the stages. This project introduces a systematic approach to identify and 
classify stages of Alzheimer's disease to assist the medical profession, particularly 
radiologist, in diagnosing the different stages of Alzheimer’s disease to reduce the time
taken for a single diagnosis. This project focuses on four different types of Alzheimer’s 
disease which are no dementia, very mild dementia, mild dementia, and moderate 
dementia. For this project, a classification model is developed to classify the stages of 
Alzheimer’s disease by processing the MRI scan image dataset from Kaggle which, 
originally from Open Access Series of Imaging Studies (OASIS). The dataset is split 
into three set where 80% of the data is for training set, 10% for the test set and the 
remaining 10% of the data is for the validation set. The method utilised for the model 
is a deep learning technique which is Convolutional Neural Network (CNN). With 50 
epochs utilised for training, the model has achieved a high accuracy with 92% of 
accuracy. The model is integrated into a web-based system designed to assist the 
radiologist to make an efficient diagnosis in interpreting imaging results without 
consuming too much time as well as to track the MRI record of the patients. For the 
future work, the optimization of the system performance is expected by incorporating 
external datasets from hospitals or other public resources to address data imbalances 
and widening the diagnostic capabilities to multiple neuro disease

This folder consists of 2 different folders which are:
1. Model - It consists of my CNN model that I utilised to train the MRI images of Alzheimer's patient. 
2. System development - The system development folder consists of my integrated web application with my CNN model.

Programming language utilised:
1. Python (including Flask Framework)
2. HTML
3. CSS
4. SQL
5. JavaScript

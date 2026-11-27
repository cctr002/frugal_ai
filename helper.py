
import numpy as np
import matplotlib.pyplot as plt
import os, sys, gc, glob, time, cv2
from threading import Thread
from PIL import Image
import albumentations as A

sys.path.insert(0,glob.glob('CIANNA/build/')[-1]) #if compiled with cmake
import CIANNA as cnn

def data_prep(nb_images_per_iter, raw_image_size, image_size, test_mode=0):
  #Data arrays are declared as global so we can work in place to reduce RAM footprint
  global raw_images, input_data, targets, input_val, targets_val

  raw_images = np.reshape(np.fromfile("asirra_bin_%d.dat"%(raw_image_size), dtype="uint8"), (25000, raw_image_size, raw_image_size,3))

  if(test_mode == 0):
    input_data = np.zeros((nb_images_per_iter,3*image_size**2), dtype="float32") #CIANNA expects "float32" arrays
    targets = np.zeros((nb_images_per_iter,2), dtype="float32")

  input_val = np.zeros((2048,3*image_size**2), dtype="float32")
  targets_val = np.zeros((2048,2), dtype="float32")


def create_augmented_batch(A_transform):

  nb_images = np.shape(input_data)[0]

  for i in range(0,nb_images):

    l_class = np.random.randint(0,2)
    l_id = np.random.randint(0,12500 - 1024)
    #Last 1024 images of each class kept only for the val/test set

    patch = raw_images[l_class*12500+l_id]
    transformed = A_transform(image=patch)
    patch_aug = transformed['image']

    l_image_size = np.shape(patch_aug)[0]

    #CIANNA expects data formated as 2D numpy arrays representing a list of flattened images (with every channel flattened after the others)
    for depth in range(0,3): #We normalize based on mean pixel value
      input_data[i,depth*l_image_size**2:(depth+1)*l_image_size**2] = (patch_aug[:,:,depth].flatten("C") - 100.0)/155.0

    targets[i,:] = 0.05 #Label smoothing during training
    targets[i,l_class] = 0.95

  return input_data, targets


def create_validation_set(A_transform):

  for i in range(0,2048):

    l_class = i // 1024

    patch = raw_images[(1+l_class)*(12500 - 1024) + i]
    transformed = A_transform(image=patch)
    patch_aug = transformed['image']

    l_image_size = np.shape(patch_aug)[0]

    for depth in range(0,3):
      input_val[i,depth*l_image_size**2:(depth+1)*l_image_size**2] = (patch_aug[:,:,depth].flatten("C") - 100.0)/155.0

    targets_val[i,:] = 0.0
    targets_val[i,l_class] = 1.0

  return input_val, targets_val


def free_data_helper():
  global raw_images, input_data, targets, input_val, targets_val
  if 'raw_images' in globals():
    del (raw_images)
  if 'input_data' in globals():
    del (input_data)
  if 'targets' in globals():
    del (targets)
  if 'input_val' in globals():
    del (input_val)
  if 'targets_val' in globals():
    del (targets_val)
  gc.collect()
  return

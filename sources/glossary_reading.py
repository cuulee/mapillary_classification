import json
import matplotlib.pyplot as plt
import os
import numpy as np
import pandas as pd
import seaborn as sns

DATA_REPOSITORY = os.path.join("..", "data")
TRAIN_LABEL_FILENAME = os.path.join(DATA_REPOSITORY, "training", "output", "labels.csv")
VALIDATION_LABEL_FILENAME = os.path.join(DATA_REPOSITORY, "validation", "output", "labels.csv")
CONFIG_FILENAME = os.path.join(DATA_REPOSITORY, "config.json")

def read_glossary(config_filename):
    """Read the Mapillary glossary stored as a json file at the data repository
    root

    """
    with open(config_filename) as config_file:
        return json.load(config_file)

def build_labels(label_file_list):
    """Build a DataFrame with the label of all dataset image (shape:
    nb_images(training+validation) * nb_labels)

    """
    # train_labels = pd.read_csv(TRAIN_LABEL_FILENAME)
    # validation_labels = pd.read_csv(VALIDATION_LABEL_FILENAME)
    labels = pd.read_csv(label_file_list[0])
    if len(label_file_list) > 1:
        for filename in label_file_list[1:]:
            # validation_labels.index = validation_labels.index + 18000
            # labels = pd.concat([train_labels, validation_labels])
            new_labels = pd.read_csv(filename)
            new_labels.index = new_labels.index + labels.shape[0]
            labels = pd.concat([labels, new_labels])
    
    return labels.drop(["old_name", "new_name",
                        "old_width", "width_ratio",
                        "old_height", "height_ratio"], axis=1)

def count_label_per_image(labels):
    """Compute the number of existing object on each dataset image

    """
    label_counter = labels.apply(sum, axis=1)
    label_counter.index = range(len(label_counter))
    return label_counter

def count_image_per_label(labels):
    """Compute the number of images for each glossary label

    """
    image_counter = labels.apply(sum, axis=0)
    image_counter.index = range(len(image_counter))
    return image_counter
  
def build_category_description(glossary, labels):
    """Build a dataframe that contains Mapillary label category description,
    with three columns "category", "subcategory" (empty if there is no subcategory), "object"
    Parameter
    ---------
    glossary: dict
    Mapillary label description with a main key 'labels', designing a list of
    dictionaries ('color', 'evaluate', 'instances', 'name', 'readable');
    'name' is under the format <category>--<subcategory(if needed)>--<object>
    """
    label_description = glossary['labels']
    label_names = [l['name'] for l in label_description]
    category_description = []
    for n in label_names:
        cur_name = n.split('--')
        if len(cur_name) == 2:
            cur_name.insert(1, '')
        category_description.append(cur_name)
    category_description = pd.DataFrame(category_description,
                                        columns=["category",
                                                 "subcategory",
                                                 "object"])
    category_description['nb_images'] = count_image_per_label(labels)
    return category_description

GLOSSARY = read_glossary(CONFIG_FILENAME)
TRAIN_LABELS = build_labels([TRAIN_LABEL_FILENAME])
NB_TRAIN_IMAGE_PER_LABEL = count_image_per_label(TRAIN_LABELS)
VAL_LABELS = build_labels([VALIDATION_LABEL_FILENAME])
NB_VAL_IMAGE_PER_LABEL = count_image_per_label(VAL_LABELS)
LABELS = build_labels([TRAIN_LABEL_FILENAME, VALIDATION_LABEL_FILENAME])
NB_IMAGE_PER_LABEL = count_image_per_label(LABELS)

def plot_nb_image_per_category(category_description):
    """Plot the number of images for each glossary label
    as histograms, grouped by categories

    """ 
    hist_palette = sns.color_palette("Set1", n_colors=8, desat=.5)
    label_categories = category_description.category.nunique()
    f, ax = plt.subplots(2, 4, figsize=(16, 8))
    ax[0][0].hist(category_description.nb_images, bins=np.linspace(0, 20000, 21), color=hist_palette[0])
    ax[0][0].set_yticks(np.linspace(0, 20, 11))
    for i in range(category_description.category.nunique()):
        cur_cat = label_categories[i]
        data = category_description.query("category==@cur_cat").nb_images
        ax[int((i+1)/4)][(i+1)%4].hist(data, bins=np.linspace(0, 20000, 21), color=hist_palette[i+1])
        ax[int((i+1)/4)][(i+1)%4].set_yticks(np.linspace(0, 20, 11))
        ax[int((i+1)/4)][(i+1)%4].text(10000, 12, cur_cat, size=14,
                                       fontweight='bold')

def plot_nb_image_per_dataset(category_description):
    """Plot the number of images per glossary label as histograms, by
    distinguishing training and validation datasets

    """
    category_description.sort_values("nb_images", ascending=False).head(6)
    hist_palette = sns.color_palette("Set1", n_colors=3, desat=.5)
    f, ax = plt.subplots(1, 3, figsize=(16, 4))
    ax[0].hist(label_count_per_image,
               bins=np.linspace(0, 66, 12), color=hist_palette[0])
    ax[0].set_xticks(np.linspace(0, 66, 12))
    ax[0].set_yticks(np.linspace(0, 12000, 13))
    ax[1].hist(label_count_per_image[:18000],
               bins=np.linspace(0, 66, 12), color=hist_palette[1])
    ax[1].set_xticks(np.linspace(0, 66, 12))
    ax[1].set_yticks(np.linspace(0, 12000, 13))
    ax[1].text(40, 10000, "train set", size=14, fontweight='bold')
    ax[2].hist(label_count_per_image[18000:],
               bins=np.linspace(0, 66, 12), color=hist_palette[2])
    ax[2].set_xticks(np.linspace(0, 66, 12))
    ax[2].set_yticks(np.linspace(0, 12000, 13))
    ax[2].text(40, 10000, "validation set",
               size=14, fontweight='bold')

def plot_fancy_nb_image_per_category(category_df):
    """ Plot the number of image per category as a seaborn barplot
    """
    f = plt.figure(figsize=(16, 6))
    image_per_label_plot = sns.barplot(category_df.object,
                                       category_df.nb_images,
                                       hue=category_df.category,
                                       palette="Set1")
    plt.ylabel("Number of images")
    plt.setp(image_per_label_plot.get_xticklabels(), rotation=80)

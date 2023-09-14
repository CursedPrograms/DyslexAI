import os
import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow.keras.layers import Dense, Reshape, Flatten, Conv2D, Conv2DTranspose, Input
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.preprocessing.image import ImageDataGenerator

def build_generator(input_dim):
    generator = Sequential()
    generator.add(Dense(7 * 7 * 256, input_dim=input_dim))
    generator.add(Reshape((7, 7, 256)))
    generator.add(Conv2DTranspose(128, (4, 4), strides=(2, 2), padding='same', activation='relu'))
    generator.add(Conv2DTranspose(64, (4, 4), strides=(2, 2), padding='same', activation='relu'))
    generator.add(Conv2D(3, (7, 7), padding='same', activation='sigmoid'))
    return generator

def build_discriminator(input_shape):
    discriminator = Sequential()
    discriminator.add(Conv2D(64, (3, 3), strides=(2, 2), padding='same', input_shape=input_shape, activation='relu'))
    discriminator.add(Conv2D(128, (3, 3), strides=(2, 2), padding='same', activation='relu'))
    discriminator.add(Flatten())
    discriminator.add(Dense(1, activation='sigmoid'))
    return discriminator

epochs = 10000
batch_size = 64
input_dim = 100
output_dir = "output_images"
model_save_dir = "saved_models"
image_shape = (28, 28, 3)       
os.makedirs(output_dir, exist_ok=True)
os.makedirs(model_save_dir, exist_ok=True)

def load_and_preprocess_dataset(target_size, batch_size):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_dir = os.path.join(script_dir, "training_data")

    datagen = ImageDataGenerator(
        rescale=1. / 255,
    )
    dataset = datagen.flow_from_directory(
        dataset_dir,         
        target_size=target_size,
        batch_size=batch_size,
        class_mode='input'       
    )
    return dataset

dataset = load_and_preprocess_dataset(image_shape[:2], batch_size)    
generator = build_generator(input_dim)
discriminator = build_discriminator(image_shape)

discriminator.compile(loss='binary_crossentropy', optimizer=tf.keras.optimizers.Adam(0.0002, 0.5), metrics=['accuracy'])

discriminator.trainable = False

gan_input = Input(shape=(input_dim,))
x = generator(gan_input)
gan_output = discriminator(x)
gan = Model(gan_input, gan_output)

gan.compile(loss='binary_crossentropy', optimizer=tf.keras.optimizers.Adam(0.0002, 0.5))

def generate_and_save_images(generator, epoch, output_dir, num_examples=16):
    os.makedirs(os.path.join(output_dir, f"epoch_{epoch}"), exist_ok=True)
    noise = np.random.normal(0, 1, (num_examples, input_dim))
    generated_images = generator.predict(noise)
    generated_images = 0.5 * generated_images + 0.5

    for i in range(num_examples):
        image = generated_images[i]
        image = (image * 255).astype(np.uint8)      
        image = Image.fromarray(image)
        image.save(os.path.join(output_dir, f"epoch_{epoch}", f"generated_image_{i}.png"))

for epoch in range(epochs):
    if epoch % 1000 == 0:
        generator_model_save_path = os.path.join(model_save_dir, f"gan_generator_weights_epoch_{epoch}.h5")
        discriminator_model_save_path = os.path.join(model_save_dir, f"gan_discriminator_weights_epoch_{epoch}.h5")
        generator.save_weights(generator_model_save_path)
        discriminator.save_weights(discriminator_model_save_path)
        print(f"Saved generator model weights to {generator_model_save_path}")
        print(f"Saved discriminator model weights to {discriminator_model_save_path}")

    for _ in range(0, len(dataset), batch_size):
        real_batch = next(dataset)
        real_images = real_batch[0]
        
        noise = np.random.normal(0, 1, (real_images.shape[0], input_dim))
        generated_images = generator.predict(noise)
        
        real_labels = np.ones((real_images.shape[0], 1))
        fake_labels = np.zeros((real_images.shape[0], 1))
        
        merged_images = np.concatenate([real_images, generated_images], axis=0)
        merged_labels = np.concatenate([real_labels, fake_labels], axis=0)
        
        indices = np.arange(merged_images.shape[0])
        np.random.shuffle(indices)
        merged_images = merged_images[indices]
        merged_labels = merged_labels[indices]

        d_loss = discriminator.train_on_batch(merged_images, merged_labels)

        noise = np.random.normal(0, 1, (real_images.shape[0], input_dim))
        g_loss = gan.train_on_batch(noise, real_labels)

    if epoch % 100 == 0:
        print(f"Epoch {epoch}/{epochs} | D Loss: {d_loss[0]} | D Accuracy: {100 * d_loss[1]} | G Loss: {g_loss}")
        generate_and_save_images(generator, epoch, output_dir)

    if epoch % 1000 == 0:
        generator_model_save_path = os.path.join(model_save_dir, f"gan_generator_weights_epoch_{epoch}.h5")
        discriminator_model_save_path = os.path.join(model_save_dir, f"gan_discriminator_weights_epoch_{epoch}.h5")
        generator.save_weights(generator_model_save_path)
        discriminator.save_weights(discriminator_model_save_path)
        print(f"Saved generator model weights to {generator_model_save_path}")
        print(f"Saved discriminator model weights to {discriminator_model_save_path}")
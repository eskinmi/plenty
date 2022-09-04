import os
import math
import shutil
import tensorflow as tf
from plenty.utils import write_json
from plenty.models.utils import gen_version_id
from plenty.models.utils import find_latest_model_version

# TODO: we have to tie the images to each class.


SRC_DATA_DIR = './data/plant-disease-dataset'
BASE_ARTIFACTS_DIR = './artifacts/disease'

FLAGS = {
    'epochs': 50,
    'learning_rate': 0.005,
    'batch_size': 64,
    'target_size': (256, 256),
    'retrain': True,
    'version_id': None,

}


class StopAtAccuracyThreshold(tf.keras.callbacks.Callback):
    def on_epoch_end(self, epoch, logs=None):
        if logs.get('val_accuracy') > 0.98:
            print(F"\nReached 98% accuracy at epoch {epoch} so cancelling training!")
            self.model.stop_training = True


def _cleanup_artifacts(artifacts_dir):
    """
    Cleanup artifacts directories, to allow new
    writes.
    """
    if artifacts_dir and os.path.exists(artifacts_dir):
        shutil.rmtree(artifacts_dir)


def main():

    with tf.device("/gpu:0"):

        if FLAGS.get('retrain'):
            if not (version_id := FLAGS.get('version_id')):
                version_id = find_latest_model_version(BASE_ARTIFACTS_DIR)
        else:
            version_id = gen_version_id()

        artifacts_dir = os.path.join(BASE_ARTIFACTS_DIR, version_id)
        train_dir = os.path.join(SRC_DATA_DIR, 'train')
        valid_dir = os.path.join(SRC_DATA_DIR, 'valid')
        target_size = FLAGS.get('target_size', (256, 256))
        batch_size = FLAGS.get('batch_size', 64)

        # Preprocess
        if not FLAGS.get('retrain'):
            _cleanup_artifacts(artifacts_dir)

        # Data Loaders
        datagen = tf.keras.preprocessing.image.ImageDataGenerator(
            preprocessing_function=tf.keras.applications.resnet_v2.preprocess_input,
            rescale=1./255
        )

        train_generator = datagen.flow_from_directory(train_dir,
                                                      target_size=target_size,
                                                      batch_size=batch_size,
                                                      class_mode='categorical'
                                                      )

        valid_generator = datagen.flow_from_directory(valid_dir,
                                                      target_size=target_size,
                                                      batch_size=batch_size,
                                                      class_mode='categorical'
                                                      )

        num_classes = len(train_generator.class_indices)

        # Model
        resnet = tf.keras.applications.ResNet152V2(weights='imagenet', include_top=False, input_shape=(256, 256, 3))
        x = resnet.output
        x = tf.keras.layers.GlobalAveragePooling2D()(x)
        x = tf.keras.layers.BatchNormalization()(x)
        x = tf.keras.layers.Dense(512, activation='relu')(x)
        x = tf.keras.layers.BatchNormalization()(x)
        x = tf.keras.layers.Dense(256, activation='relu')(x)
        x = tf.keras.layers.BatchNormalization()(x)
        x = tf.keras.layers.Dense(128, activation='relu')(x)
        x = tf.keras.layers.BatchNormalization()(x)
        out = tf.keras.layers.Dense(num_classes, activation='softmax')(x)
        model = tf.keras.models.Model(inputs=resnet.input, outputs=out)

        for layer in model.layers:
            layer.trainable = True

        if FLAGS.get('retrain'):
            model = tf.keras.models.load_model(
                os.path.join(artifacts_dir, 'ckpt', 'plant-disease.h5')
            )
        else:
            optimizer = tf.keras.optimizers.Adam(lr=FLAGS['learning_rate'])
            model.compile(loss='categorical_crossentropy',
                          optimizer=optimizer,
                          metrics=['accuracy']
                          )

        # Callbacks
        acc_stopper = StopAtAccuracyThreshold()

        checkpoint = tf.keras.callbacks.ModelCheckpoint(
            os.path.join(artifacts_dir, 'ckpt', 'plant-disease.h5'),
            monitor='val_accuracy',
            save_best_only=True,
            save_weights_only=False,
            verbose=1,
            mode='auto',
            period=1
        )

        early_stop = tf.keras.callbacks.EarlyStopping(
            monitor='val_accuracy',
            min_delta=.0001,
            patience=5,
            verbose=1,
            mode='auto',
            baseline=None,
            restore_best_weights=True
        )

        reduce_lr = tf.keras.callbacks.ReduceLROnPlateau(
            monitor='val_accuracy',
            factor=math.sqrt(.1),
            patience=5,
            verbose=1,
            mode='auto',
            min_delta=.0001,
            cooldown=0,
            min_lr=0.00001
        )

        # Train
        hist = model.fit(train_generator,
                         steps_per_epoch=len(train_generator),
                         validation_data=valid_generator,
                         validation_steps=len(valid_generator),
                         epochs=FLAGS['epochs'],
                         callbacks=[acc_stopper,
                                    checkpoint,
                                    early_stop,
                                    reduce_lr
                                    ]
                         )

        # Write Model & Artifacts
        model.save(os.path.join(artifacts_dir, 'plant-disease.h5'))
        write_json(hist.history, os.path.join(artifacts_dir, 'train_hist', 'train_hist.json'))
        write_json(train_generator.class_indices, os.path.join(artifacts_dir, 'indices.json'))
        write_json(FLAGS, os.path.join(artifacts_dir, 'params.json'))


if __name__ == '__main__':
    main()

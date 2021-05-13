import os
from . import logger, cfg

raise NotImplementedError('The Subject Module is Deprecated.')

folder = cfg['Subject']['folder']


def create(path):
    ''' Create [path], do nothing if it exists

    Args:
    - @path: The path to be created.
    '''
    if not os.path.isdir(path):
        os.mkdir(path)
        logger.debug(f'Folder is created: "{path}"')
    else:
        logger.debug(f'Folder exists: "{path}"')


class BCISubject(object):
    '''Subject Folder Manager '''

    def __init__(self, subjectID, folder=folder):
        ''' Initialize the subject's folder

        Args:
        - @subjectID: The ID of the subject, it should be unique;
        - @folder: The folder of subjects, it exists in prior, it has default value.
        '''
        if not os.path.isdir(folder):
            logger.error(f'Folder does not exist: "{folder}"')
            raise FileNotFoundError(f'Folder not found: "{folder}"')

        self.subjectID = subjectID
        subjectFolder = os.path.join(folder, subjectID)

        create(subjectFolder)

        self.subjectFolder = subjectFolder
        self.subFolders = self.generate_folders()
        logger.info(f'Initialized subject with folder of {subjectFolder}')

    def generate_folders(self):
        ''' Generate the necessary subfolders '''
        folders = dict(
            training=os.path.join(self.subjectFolder, 'training'),
            youbiaoqian=os.path.join(self.subjectFolder, 'youbiaoqian'),
            wubiaoqian=os.path.join(self.subjectFolder, 'wubiaoqian'),
        )

        for p in folders:
            create(folders[p])

        return folders

    def get_training_path(self):
        ''' Get the path of trained model and training data '''
        path = dict(
            data=os.path.join(self.subFolders['training'], 'data.npy'),
            model=os.path.join(self.subFolders['training'], 'model.dump')
        )

        if os.path.isfile(path['data']):
            logger.warning(
                'Training file of {} exists, it may be overridden'.format(path['data']))

        if os.path.isfile(path['model']):
            logger.warning(
                'Training model of {} exists, it may be overridden'.format(path['model']))

        return path

    def set_youbiaoqian(self, idx):
        ''' Setup the path of the idx experiment of the wubiaoqian online experiment

        Args:
        - @idx: The count of the experiment.
        '''
        path = os.path.join(self.subFolders['youbiaoqian'], f'{idx}')
        create(path)

    def get_youbiaoqian_path(self, idx):
        ''' Get the path of the updated model and online data by the idx

        Args:
        - @idx: The count of the experiment.
        '''
        path = dict(
            data=os.path.join(
                self.subFolders['youbiaoqian'], f'{idx}', 'data.npy'),
            model=os.path.join(
                self.subFolders['training'], 'model.dump'),
            model_update=os.path.join(
                self.subFolders['youbiaoqian'], f'{idx}', 'model.dump')
        )

        if os.path.isfile(path['data']):
            logger.warning(
                'Training file of {} exists, it may be overridden'.format(path['data']))

        if not os.path.isfile(path['model']):
            msg = 'Can not find model of {}'.format(path['model'])
            logger.error(msg)
            raise FileNotFoundError(msg)

        if os.path.isfile(path['model_update']):
            logger.warning(
                'Training model update of {} exists, it may be overridden'.format(path['model_update']))

        return path

    def set_wubiaoqian(self, idx):
        ''' Setup the path of the idx experiment of the wubiaoqian online experiment

        Args:
        - @idx: The count of the experiment.
        '''
        path = os.path.join(self.subFolders['wubiaoqian'], f'{idx}')
        create(path)

    def get_wubiaoqian_path(self, idx):
        ''' Get the path of the updated model and online data by the idx

        Args:
        - @idx: The count of the experiment.
        '''
        path = dict(
            data=os.path.join(
                self.subFolders['wubiaoqian'], f'{idx}', 'data.npy'),
            model=os.path.join(self.subFolders['training'], 'model.dump')
        )

        if os.path.isfile(path['data']):
            logger.warning(
                'Training file of {} exists, it may be overridden'.format(path['data']))

        if not os.path.isfile(path['model']):
            msg = 'Can not find model of {}'.format(path['model'])
            logger.error(msg)
            raise FileNotFoundError(msg)

        return path

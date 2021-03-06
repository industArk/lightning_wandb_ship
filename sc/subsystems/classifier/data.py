# Copyright 2022 Arkadiusz Choruży


from typing import Tuple, Optional
from pathlib import Path
import pandas as pd
from pytorch_lightning import LightningDataModule
from torch.utils.data import DataLoader, Dataset
from torch import from_numpy, unsqueeze
from sklearn.utils import shuffle
from numpy import float32, asarray
from PIL import Image

DATA_DIR = Path(__file__).parent/'../../../data/images'
LABELS_DIR = Path(__file__).parent/'../../../data/labels.csv'

RANDOM_STATE = 112

# categories in data CSV are 1-5 so need to be converted by -1 in further works
categories = {  
    1: 'cargo',
    2: 'navy',
    3: 'carrier',
    4: 'cruise',
    5: 'tanker'
}


class ShipDataset(Dataset):
    def __init__(self, file_data: Tuple, img_size: int):
        self.file_paths = [DATA_DIR/path for path in file_data[0]]
        self.labels = [label for label in file_data[1]]
        self.img_size = img_size
        
    def __len__(self):
        return len(self.file_paths)
    
    def __getitem__(self, idx):
        path = self.file_paths[idx]
        label = self.labels[idx] - 1

        img = Image.open(path).resize((self.img_size, self.img_size), resample=Image.Resampling.BILINEAR)
        img = img.convert(mode='L')
        np_img = asarray(img, dtype=float32) /255
        tens = from_numpy(np_img)
        return tens, label


class ShipDataModule(LightningDataModule):
    def __init__(self, split: Tuple[float], bs: int, img_size: int):
        super().__init__()
        self.split = split
        self.bs = bs
        self.num_workers = 4
        self.img_size = img_size

    def prepare_data(self):
        df = pd.read_csv(LABELS_DIR)
        shuffled = shuffle(df, random_state=RANDOM_STATE)

        num_files = len(shuffled)
        split_train_valid = num_files - int(num_files*(self.split[0]+self.split[1]))
        split_valid_test = num_files - int(num_files*self.split[1])

        X = shuffled['image'].values
        y = shuffled['category'].values

        self.train_list = (X[:split_train_valid], y[:split_train_valid])
        self.test_list = (X[split_train_valid:split_valid_test], y[split_train_valid:split_valid_test])
        self.valid_list = (X[split_valid_test:], y[split_valid_test:])

    def setup(self, stage: Optional[str] = None):
        self.train_dataset = ShipDataset(self.train_list, self.img_size)
        self.valid_dataset = ShipDataset(self.valid_list, self.img_size)
        self.test_dataset = ShipDataset(self.test_list, self.img_size)

    def train_dataloader(self):
        return DataLoader(self.train_dataset, batch_size=self.bs, num_workers=self.num_workers)

    def val_dataloader(self):
        return DataLoader(self.valid_dataset, batch_size=self.bs, num_workers=self.num_workers)

    def test_dataloader(self):
        return DataLoader(self.test_dataset, batch_size=self.bs, num_workers=self.num_workers)
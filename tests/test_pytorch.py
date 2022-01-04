import unittest
import pickle
import tempfile
from pathlib import Path
import torch
from torch.utils.data import Dataset, DataLoader

from ffrecord import FileWriter
from ffrecord.torch import Dataset as FFDataset, DataLoader as FFDataLoader


class DummyDataset(Dataset):
    def __init__(self, n):
        self.n = n

    def __len__(self):
        return self.n

    def __getitem__(self, index):
        return (index * 2, index * 3)


class DummyFireFlyerDataset(FFDataset):
    def process(self, indexes, data):
        processed_data = []
        for bytes_ in data:
            sample = pickle.loads(bytes_)
            processed_data.append(sample)

        return processed_data


class TestDataLoader(unittest.TestCase):
    def subtest_dataloader(self, num_workers):
        _, file = tempfile.mkstemp(suffix='.ffr')
        n = 100

        dataset = DummyDataset(n)
        dataloader = DataLoader(
            dataset,
            batch_size=8,
            shuffle=False,
            num_workers=4,
        )

        # dump dataset
        writer = FileWriter(file, len(dataset))
        for i in range(len(dataset)):
            data = pickle.dumps(dataset[i])
            data = bytearray(data)
            writer.write_one(data)
        writer.close()
        # load dataset
        ffdataset = DummyFireFlyerDataset(file)
        ffdataloader = FFDataLoader(
            ffdataset,
            batch_size=8,
            shuffle=False,
            num_workers=num_workers,
        )

        assert len(dataloader) == len(ffdataloader)
        for batch1, batch2 in zip(dataloader, ffdataloader):
            print(batch1[0], batch2[0])
            assert torch.equal(batch1[0], batch2[0])
            assert torch.equal(batch1[1], batch2[1])

        Path(file).unlink()

    def test_single_process(self):
        self.subtest_dataloader(0)

    def test_multiple_processes(self):
        self.subtest_dataloader(8)


if __name__ == '__main__':
    torch.multiprocessing.set_start_method('spawn')
    unittest.main()

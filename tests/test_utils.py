import os

if not os.path.isdir('utils'):
    if os.path.isdir('../utils'):
        os.chdir("..")
    else:
        raise FileNotFoundError("Can't find utils folder, you are in the wrong folder.")


from utils import loaders

def test_currency_pair_exists():
    assert loaders.currency_pair_exists("btcusd"), "Test currency that exist failed"
    assert not loaders.currency_pair_exists("febsjdbfxh"), "Test currency that not exist failed"

if __name__ == "__main__":
    test_currency_pair_exists()
    print("Test currency pair succesfull")
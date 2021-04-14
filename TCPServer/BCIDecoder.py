'''
The BCI Decoding Object.
'''


class BCIDecoder(object):
    '''Class of BCI Decoder'''

    def __init__(self):
        pass

    def fit(self, X):
        '''The method of fitting the decoder.

        Args:
        - X: The feature of training samples, the shape is (......).

        需要把分类器训练的方法写在这里，
        - X是EEG设备出来的原始数据，很长，有多个TRIAL；
        - X里包含标签导联，需要程序自己提出来；
        - 所有的预处理、分类器训练都在这里完成。
        '''
        return self

    def predict(self, X):
        '''The method of predict using the features.

        Args:
        - X: The feature of testing samples, the shape is (......).

        Outs:
        - The computed labels, the shape is (......).

        需要分类器测试方法写在这里，
        - X是待测的脑电数据，也是EEG设备直接出来的；
        - X长度可以指定，现在实验的约定是4秒；
        - 程序应返回估计出的标签。
        '''
        return 1

    def load(self, decoderpath):
        '''Load the model from [decoderpath].

        Args:
        - decoderpath: The path of the decoder.

        这个代码需要从指定位置导入训练好的模型。
        '''
        pass

    def save(self, decoderpath):
        '''Save the model to [decoderpath].

        Args:
        - decoderpath: The path of the decoder.

        这个代码需要把训练好的模型存储到指定位置。
        '''
        pass

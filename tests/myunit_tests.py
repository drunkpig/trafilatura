import logging
import os
import sys

import pytest
from lxml import etree, html
from lxml import html

try:
    from cchardet import detect
except ImportError:
    from charset_normalizer import detect

# language detection
try:
    import py3langid

    LANGID_FLAG = True
except ImportError:
    LANGID_FLAG = False

import trafilatura.htmlprocessing
from trafilatura import (bare_extraction, baseline, extract, html2txt,
                         process_record, utils, xml)
from trafilatura.core import (Extractor, handle_formatting, handle_image,
                              handle_lists, handle_paragraphs, handle_quotes,
                              handle_table, handle_textelem, sanitize_tree,
                              trim)
from trafilatura.external import try_justext
from trafilatura.filters import textfilter
from trafilatura.meta import reset_caches
from trafilatura.metadata import Document
from trafilatura.settings import DEFAULT_CONFIG, TAG_CATALOG, use_config
from trafilatura import fetch_url, extract
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

TEST_DIR = os.path.abspath(os.path.dirname(__file__))
RESOURCES_DIR = os.path.join(TEST_DIR, 'resources')
SAMPLE_META = Document()

ZERO_CONFIG = DEFAULT_CONFIG
ZERO_CONFIG['DEFAULT']['MIN_OUTPUT_SIZE'] = '0'
ZERO_CONFIG['DEFAULT']['MIN_EXTRACTED_SIZE'] = '0'

NEW_CONFIG = use_config(filename=os.path.join(RESOURCES_DIR, 'newsettings.cfg'))

MOCK_PAGES = {
    'http://exotic_tags': 'exotic_tags.html',
}

DEFAULT_OPTIONS = Extractor(*[False] * 11)
DEFAULT_OPTIONS.config = DEFAULT_CONFIG

@pytest.mark.skip(reason="no way of currently testing this")
def test_images():
    '''Test image extraction function'''
    # file type
    assert utils.is_image_file('test.jpg') is True
    assert utils.is_image_file('test.txt') is False
    # tag with attributes
    assert handle_image(html.fromstring('<img src="test.jpg"/>')) is not None
    assert handle_image(html.fromstring('<img data-src="test.jpg" alt="text" title="a title"/>')) is not None
    assert handle_image(html.fromstring('<img other="test.jpg"/>')) is None
    # HTML conversion
    assert handle_textelem(etree.Element('graphic'), [], DEFAULT_OPTIONS) is None
    with open(os.path.join(RESOURCES_DIR, 'http_sample.html')) as f:
        teststring = f.read()
    assert '![Example image](test.jpg)' not in extract(teststring)
    assert '![Example image](test.jpg)' in extract(teststring, include_images=True, no_fallback=True)
    assert '<graphic src="test.jpg" title="Example image"/>' in extract(teststring, include_images=True, no_fallback=True, output_format='xml', config=ZERO_CONFIG)
    assert extract('<html><body><article><img data-src="test.jpg" alt="text" title="a title"/></article></body></html>', include_images=True, no_fallback=True) == '![a title text](test.jpg)'

    # CNN example
    mydoc = html.fromstring(
        '<img class="media__image media__image--responsive" alt="Harry and Meghan last March, in their final royal engagement." data-src-mini="//cdn.cnn.com/cnnnext/dam/assets/210307091919-harry-meghan-commonwealth-day-small-169.jpg" data-src-xsmall="//cdn.cnn.com/cnnnext/dam/assets/210307091919-harry-meghan-commonwealth-day-medium-plus-169.jpg" data-src-small="//cdn.cnn.com/cnnnext/dam/assets/210307091919-harry-meghan-commonwealth-day-large-169.jpg" data-src-medium="//cdn.cnn.com/cnnnext/dam/assets/210307091919-harry-meghan-commonwealth-day-exlarge-169.jpg" data-src-large="//cdn.cnn.com/cnnnext/dam/assets/210307091919-harry-meghan-commonwealth-day-super-169.jpg" data-src-full16x9="//cdn.cnn.com/cnnnext/dam/assets/210307091919-harry-meghan-commonwealth-day-full-169.jpg" data-src-mini1x1="//cdn.cnn.com/cnnnext/dam/assets/210307091919-harry-meghan-commonwealth-day-small-11.jpg" data-demand-load="loaded" data-eq-pts="mini: 0, xsmall: 221, small: 308, medium: 461, large: 781" src="//cdn.cnn.com/cnnnext/dam/assets/210307091919-harry-meghan-commonwealth-day-exlarge-169.jpg" data-eq-state="mini xsmall small medium" data-src="//cdn.cnn.com/cnnnext/dam/assets/210307091919-harry-meghan-commonwealth-day-exlarge-169.jpg">')
    myimage = handle_image(mydoc)
    assert myimage is not None and 'alt' in myimage.attrib and 'src' in myimage.attrib
    # modified CNN example
    mydoc = html.fromstring(
        '<img class="media__image media__image--responsive" alt="Harry and Meghan last March, in their final royal engagement." data-src-mini="//cdn.cnn.com/cnnnext/dam/assets/210307091919-harry-meghan-commonwealth-day-small-169.jpg" data-src-xsmall="//cdn.cnn.com/cnnnext/dam/assets/210307091919-harry-meghan-commonwealth-day-medium-plus-169.jpg" data-src-small="//cdn.cnn.com/cnnnext/dam/assets/210307091919-harry-meghan-commonwealth-day-large-169.jpg" data-src-medium="//cdn.cnn.com/cnnnext/dam/assets/210307091919-harry-meghan-commonwealth-day-exlarge-169.jpg" data-src-large="//cdn.cnn.com/cnnnext/dam/assets/210307091919-harry-meghan-commonwealth-day-super-169.jpg" data-src-full16x9="//cdn.cnn.com/cnnnext/dam/assets/210307091919-harry-meghan-commonwealth-day-full-169.jpg" data-src-mini1x1="//cdn.cnn.com/cnnnext/dam/assets/210307091919-harry-meghan-commonwealth-day-small-11.jpg" data-demand-load="loaded" data-eq-pts="mini: 0, xsmall: 221, small: 308, medium: 461, large: 781">')
    myimage = handle_image(mydoc)
    assert myimage is not None and 'alt' in myimage.attrib and 'src' in myimage.attrib and myimage.get('src').startswith('http')


@pytest.mark.skip(reason="no way of currently testing this")
def test_myimage():
    """
    扩展测试，为了提升对正文中图片的召回率，对is_image_file和handle_image进行了修改
    """
    # https://prerelease.barnesandnoble.com/w/ct-atlas-of-adult-congenital-heart-disease-wojciech-mazur/1136772882?ean=9781447150886
    doc_str = """
    <html><body><article><img id="pdpMainImage" class="full-shadow ResolveComplete pdpImgLoadCompleted" tabindex="-1" src="https://prodimage.images-bn.com/lf?set=key%5Bresolve.pixelRatio%5D,value%5B1%5D&amp;set=key%5Bresolve.width%5D,value%5B600%5D&amp;set=key%5Bresolve.height%5D,value%5B10000%5D&amp;set=key%5Bresolve.imageFit%5D,value%5Bcontainerwidth%5D&amp;set=key%5Bresolve.allowImageUpscaling%5D,value%5B0%5D&amp;set=key%5Bresolve.format%5D,value%5Bwebp%5D&amp;source=url%5Bhttps://prodimage.images-bn.com/pimages/9781447150886_p0_v2_s600x595.jpg%5D&amp;scale=options%5Blimit%5D,size%5B600x10000%5D&amp;sink=format%5Bwebp%5D" alt="CT Atlas of Adult Congenital Heart Disease" itemprop="image" data-bottom-align=""/></article></body></html>
    """

    image_doc = """
    <img id="pdpMainImage" class="full-shadow ResolveComplete pdpImgLoadCompleted" tabindex="-1" src="https://prodimage.images-bn.com/lf?set=key%5Bresolve.pixelRatio%5D,value%5B1%5D&amp;set=key%5Bresolve.width%5D,value%5B600%5D&amp;set=key%5Bresolve.height%5D,value%5B10000%5D&amp;set=key%5Bresolve.imageFit%5D,value%5Bcontainerwidth%5D&amp;set=key%5Bresolve.allowImageUpscaling%5D,value%5B0%5D&amp;set=key%5Bresolve.format%5D,value%5Bwebp%5D&amp;source=url%5Bhttps://prodimage.images-bn.com/pimages/9781447150886_p0_v2_s600x595.jpg%5D&amp;scale=options%5Blimit%5D,size%5B600x10000%5D&amp;sink=format%5Bwebp%5D" alt="CT Atlas of Adult Congenital Heart Disease" itemprop="image" data-bottom-align=""/>
    """
    image_url = "https://prodimage.images-bn.com/lf?set=key%5Bresolve.pixelRatio%5D,value%5B1%5D&set=key%5Bresolve.width%5D,value%5B600%5D&set=key%5Bresolve.height%5D,value%5B10000%5D&set=key%5Bresolve.imageFit%5D,value%5Bcontainerwidth%5D&set=key%5Bresolve.allowImageUpscaling%5D,value%5B0%5D&set=key%5Bresolve.format%5D,value%5Bwebp%5D&source=url%5Bhttps://prodimage.images-bn.com/pimages/9781447150886_p0_v2_s600x595.jpg%5D&scale=options%5Blimit%5D,size%5B600x10000%5D&sink=format%5Bwebp%5D"
    assert utils.is_image_file(image_url) is True

    mydoc = html.fromstring(image_doc)
    myimage = handle_image(mydoc)
    assert myimage is not None and 'alt' in myimage.attrib and 'src' in myimage.attrib and myimage.get('src').startswith('https')


def test_extract():
    url = "https://new.qq.com/rain/a/20230829A03IM600" # tx新闻，含一张文中图片
    # url = "https://victoriyaclub.com/anna85-ID-126-38-years-old/"
    # url = "https://www.sohu.com/a/716249036_114988"
    url = "https://k.sina.com.cn/article_5044281310_12ca99fde0200216bi.html?from=news&subch=onews" # 多图
    # url = "https://victoriyaclub.com/anna85-ID-126-37-years-old/"
    # url = "https://zh.wikipedia.org/wiki/%E5%94%90%E5%AE%8B%E5%85%AB%E5%A4%A7%E5%AE%B6" # table错乱
    #url = "https://www.msn.com/en-in/news/techandscience/chandrayaan-3-completes-lunar-bound-manoeuvre-separation-tomorrow-final-steps-explained/ar-AA1fkNbL?ocid=msedgntp&cvid=08587f33983f443583fc5bff9df5c7ff&ei=42" # msdn
    #url = "http://www.paulgraham.com/greatwork.html" # https://github.com/adbar/trafilatura/issues/396
    # url = "http://www.magickeys.com/books/gingerbread/index.html"
    url = "https://new.qq.com/rain/a/20230831A055CQ00"
    url = "https://www.thefp.com/p/an-illustrated-guide-to-self-censorship" # 不工作
    url = "https://openstax.org/books/anatomy-and-physiology/pages/6-1-the-functions-of-the-skeletal-system#fig-ch06_01_04"
    url = "https://mp.weixin.qq.com/s/gd7LKWFsVD8WJDU2CTf9LQ"
    url = "https://mp.weixin.qq.com/s?__biz=MzAwMjk0Mzc5OA==&mid=2247490670&idx=1&sn=a28a24ec83e516a2796ce64dcafd405c&chksm=9ac3e237adb46b2170dec9a53f61847b00cb019e1238d28d7365eabfdfc40cf3a36b8d36448e&scene=132&exptype=timeline_recommend_article_extendread_samebiz#wechat_redirect"
    downloaded = fetch_url(url)
    # tree = html.fromstring(downloaded)
    # tree.make_links_absolute(url)

    format = "txt"
    result = trafilatura.extract(downloaded, url, output_format=format, include_images=True,include_formatting=True)
    with open(f"d:/test.{format}.md", "w", encoding="utf-8") as f:
        f.write(result)

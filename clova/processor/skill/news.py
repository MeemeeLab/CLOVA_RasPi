import re
import requests
import time

from typing import Optional

from bs4 import BeautifulSoup

from clova.general.globals import global_config_prov

from clova.processor.skill.base_skill import BaseSkillProvider

from clova.general.logger import BaseLogger

CATEGORY_URL_TABLE = {
    "トップ": "https://news.yahoo.co.jp/",
    "国内": "https://news.yahoo.co.jp/categories/domestic",
    "国際": "https://news.yahoo.co.jp/categories/world",
    "ビジネス": "https://news.yahoo.co.jp/categories/business",
    "エンタメ": "https://news.yahoo.co.jp/categories/entertainment",
    "スポーツ": "https://news.yahoo.co.jp/categories/sports",
    "科学": "https://news.yahoo.co.jp/categories/science",
    "地域": "https://news.yahoo.co.jp/categories/local",
    "コンピュータ": "https://news.yahoo.co.jp/categories/it",
    "インターネット": "https://news.yahoo.co.jp/categories/internet",
    "社会": "https://news.yahoo.co.jp/categories/society",
}

NEWS_URL_STRING = "https://news.yahoo.co.jp/"

# ==================================
#       ニュースリーダークラス
# ==================================


class NewsSkillProvider(BaseSkillProvider, BaseLogger):
    # コンストラクタ
    def __init__(self) -> None:
        super().__init__()

        self._news_count = 0

    # デストラクタ
    def __del__(self) -> None:
        super().__del__()

    def get_prompt_addition(self) -> str:
        return "NewsSkillProvider: これは最新のニュースを返答するスキルです。 フォーマット: `CALL_NEWS <トップ|国内|国際|ビジネス|エンタメ|スポーツ|科学|地域|コンピュータ|インターネット|社会>`"

    # ニュース 質問に答える。ニュースの問い合わせではなければ None を返す
    def try_get_answer(self, prompt: str, use_stub: bool, **kwarg: str) -> Optional[str]:
        # 前回がニュースで無ければ
        if (self._news_count == 0):
            if not use_stub:
                # 新スキルコードをサポートしている場合、前処理しない
                # Bardはかなり頭が悪いので新スキルコードを使えない
                return None

            self.log("try_get_answer", "stub! expect unreliable response from skill")

            match = re.match("(.+)ニュース.*教えて", prompt)
            if match is not None:
                category = match.group(1)
                if category in CATEGORY_URL_TABLE:
                    return self._start(category)
                else:
                    answer_text = "ニュースのカテゴリーを認識できませんでした。"
                    self.log("try_get_answer", "No Category for NEWS")
                    self._news_count = 0
                    return None
            else:
                # 該当がない場合は空で返信
                self.log("try_get_answer", "No Keyword for NEWS")
                self._news_count = 0
                return None
        # 前回がニュースであれば番号を選択する
        else:
            if (("終わり" in prompt) or ("おわり" in prompt)):
                answer_text = "ニュースを終わります"
                self._news_count = 0
                return (answer_text)

            match = re.match("(\\d+)", prompt)
            if match is not None:
                selected_num = int(match.group(1))
                if (1 <= selected_num <= self._news_count):
                    # 選択された番号から URL を取得する
                    selected_news = self._news_list[selected_num - 1]
                    news_url = selected_news["href"]
                    self.log("try_get_answer", "URL={}".format(news_url))

                    # URL からデータを取得して、さらにその記事全文の URL を取得する
                    response = requests.get(news_url)
                    soup = BeautifulSoup(response.content, "html.parser")
                    sub_soup = soup.select("a:contains('記事全文を読む')")[0]
                    sub_link = sub_soup.attrs["href"]
                    self.log("try_get_answer", "Sub URL={}".format(sub_link))

                    # URL から記事本文を取得する。
                    detail_body = requests.get(sub_link)
                    detail_soup = BeautifulSoup(detail_body.text, "html.parser")

                    # 記事本文のタイトルを表示する
                    assert detail_soup.title
                    self.log("try_get_answer", "Detail title = {}".format(detail_soup.title.text))

                    # class属性の中に「Direct」が含まれる行を抽出する
                    direct = detail_soup.find(class_=re.compile("Direct"))
                    assert direct
                    news_detail = direct.text

                    if global_config_prov.verbose():
                        self.log("try_get_answer", "Detail text ={}".format(news_detail))

                    return news_detail
                else:
                    answer_text = "番号が不正または範囲外です。\n詳細を知りたい番号を1から{}で選んでください。\n終了するには終わりと言ってください。".format(str(self._news_count))
                    return answer_text
        return None

    def _start(self, category: str) -> str:
        url = CATEGORY_URL_TABLE[category]
        self.log("_start", "Getting {} News!!".format(category))
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        news_list = soup.find_all(href=re.compile("news.yahoo.co.jp/pickup"))
        news_headlines = "以下のニュースがあります。"

        elements = soup.find_all(href=re.compile("news.yahoo.co.jp/pickup"))
        num = 1
        for element in elements:
            # ニューステキスト
            news_text = element.getText()
            # 後で、番号を指定するとニュースを読み上げる様に拡張するために LINK も保存しておく
            # link = element.attrs["href"]
            news_headlines += "{}. {}".format(str(num), news_text) + "\n"
            num += 1
        self.log("_start", news_headlines)
        self._news_count = num - 1
        self._news_list = news_list
        news_headlines += "詳細を知りたい番号を1から{}で選んでください。\n".format(str(self._news_count))

        return news_headlines

    def try_get_answer_post_process(self, response: str) -> Optional[str]:
        if not response.startswith("CALL_NEWS"):
            return None

        args = response.split("\n")[0].split(" ")
        return self._start(args[1])


# ==================================
#       本クラスのテスト用処理
# ==================================


def module_test() -> None:
    news = NewsSkillProvider()
    news_text = news.try_get_answer("国際ニュースを教えて", True)
    print(news_text)
    time.sleep(5)

    news_text = news.try_get_answer("1番", True)
    print(news_text)


# ==================================
# 本モジュールを直接呼出した時の処理
# ==================================
if __name__ == "__main__":
    # 直接呼び出したときは、モジュールテストを実行する。
    module_test()

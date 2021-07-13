from bs4 import BeautifulSoup
from threading import Thread
import requests
from urllib.parse import urlparse,urljoin

class PageFetcher(Thread):
    def __init__(self, obj_scheduler):
        self.obj_scheduler = obj_scheduler


    def request_url(self,obj_url):
        """
            Faz a requisição e retorna o conteúdo em binário da URL passada como parametro
            obj_url: Instancia da classe ParseResult com a URL a ser requisitada.
        """
        response = requests.get(obj_url.geturl(), headers={'user-agent': self.obj_scheduler.str_usr_agent})

        if 'html' not in response.headers['content-type']:
            return None

        return response.content


    def discover_links(self,obj_url,int_depth,bin_str_content):
        """
        Retorna os links do conteúdo bin_str_content da página já requisitada obj_url
        """
        soup = BeautifulSoup(bin_str_content, features="lxml")
        depth = int_depth
        url = ''

        for link in soup.select('a'):
            if link.get("href"): url = link["href"]
            if "http" not in url: url = obj_url.geturl() + "/" + url

            new_url = urlparse(url)
            if obj_url.netloc in url:
                depth = int_depth + 1
            else:
                depth = 0

            yield new_url, depth


    def crawl_new_url(self):
        """
            Coleta uma nova URL, obtendo-a do escalonador
        """
        next_url = self.obj_scheduler.get_next_url()

        if next_url[0]:
            self.obj_scheduler.count_fetched_page()

            if self.request_url(next_url[0]):
                print(f"{next_url[0].geturl()}\nProfundidade {next_url[1]}\n")
                next_urls = self.discover_links(next_url[0], next_url[1], self.request_url(next_url[0]))
                [self.obj_scheduler.add_new_page(obj_url, int_depth) for obj_url, int_depth in next_urls]
                return True

            return False

    def run(self):
        """
            Executa coleta enquanto houver páginas a serem coletadas
        """
        while not self.obj_scheduler.has_finished_crawl():
            self.crawl_new_url()

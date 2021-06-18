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
        headers = {'user-agent': self.obj_scheduler.str_usr_agent}
        response = requests.get(obj_url.geturl(), headers=headers)
        
        if 'html' not in response.headers['content-type']:
            return None
        
        return response.content  


    def discover_links(self,obj_url,int_depth,bin_str_content):
        """
        Retorna os links do conteúdo bin_str_content da página já requisitada obj_url
        """
        soup = BeautifulSoup(bin_str_content,features="lxml")
        for link in soup.select('a'):
            obj_new_url = urlparse(urljoin(obj_url.geturl(), link['href']))
            int_new_depth = 0
            
            if(obj_new_url.netloc == obj_url.netloc):
                int_new_depth = int_depth + 1
            
            yield obj_new_url, int_new_depth

    def crawl_new_url(self):
        """
            Coleta uma nova URL, obtendo-a do escalonador
        """
        pass

    def run(self):
        """
            Executa coleta enquanto houver páginas a serem coletadas
        """
        pass

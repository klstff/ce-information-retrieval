from util.threads import synchronized
from collections import OrderedDict
from .domain import Domain
from urllib.parse import urlparse
import urllib.robotparser
import time

class Scheduler():
    #tempo (em segundos) entre as requisições
    TIME_LIMIT_BETWEEN_REQUESTS = 20

    def __init__(self,str_usr_agent,int_page_limit,int_depth_limit,arr_urls_seeds):
        """
            Inicializa o escalonador. Atributos:
                - `str_usr_agent`: Nome do `User agent`. Usualmente, é o nome do navegador, em nosso caso,  será o nome do coletor (usualmente, terminado em `bot`)
                - `int_page_limit`: Número de páginas a serem coletadas
                - `int_depth_limit`: Profundidade máxima a ser coletada
                - `int_page_count`: Quantidade de página já coletada
                - `dic_url_per_domain`: Fila de URLs por domínio (explicado anteriormente)
                - `set_discovered_urls`: Conjunto de URLs descobertas, ou seja, que foi extraída em algum HTML e já adicionadas na fila - mesmo se já ela foi retirada da fila. A URL armazenada deve ser uma string.
                - `dic_robots_per_domain`: Dicionário armazenando, para cada domínio, o objeto representando as regras obtidas no `robots.txt`
        """
        self.str_usr_agent = str_usr_agent
        self.int_page_limit = int_page_limit
        self.int_depth_limit = int_depth_limit
        self.int_page_count = 0

        self.dic_url_per_domain = OrderedDict()
        self.set_discovered_urls = set()
        self.dic_robots_per_domain = {}
        [self.add_new_page(urlparse(url), 0) for url in arr_urls_seeds]


    @synchronized
    def count_fetched_page(self):
        """
            Contabiliza o número de paginas já coletadas
        """
        self.int_page_count += 1

    def has_finished_crawl(self):
        """
            Verifica se finalizou a coleta
        """
        if(self.int_page_count > self.int_page_limit):
            return True
        return False


    @synchronized
    def can_add_page(self,obj_url,int_depth):
        """
            Retorna verdadeiro caso profundade for menor que a maxima
            e a url não foi descoberta ainda
        """
        if int_depth < self.int_depth_limit and obj_url.geturl() not in self.set_discovered_urls:
            return True
        return False


    @synchronized
    def add_new_page(self,obj_url,int_depth):
        """
            Adiciona uma nova página
            obj_url: Objeto da classe ParseResult com a URL a ser adicionada
            int_depth: Profundidade na qual foi coletada essa URL
        """
        #https://docs.python.org/3/library/urllib.parse.html
        if self.can_add_page(obj_url,int_depth):

            if obj_url.netloc not in self.dic_url_per_domain:
                domain = Domain(obj_url.netloc, self.TIME_LIMIT_BETWEEN_REQUESTS)
                self.dic_url_per_domain[domain] = [(obj_url,int_depth)]
            else:
                self.dic_url_per_domain[obj_url.netloc].append((obj_url,int_depth))

            self.set_discovered_urls.add(obj_url.geturl())
            return True

        return False


    @synchronized
    def get_next_url(self):
        """
        Obtem uma nova URL por meio da fila. Essa URL é removida da fila.
        Logo após, caso o servidor não tenha mais URLs, o mesmo também é removido.
        """
        for domain, url_list in self.dic_url_per_domain.items():
            if domain.is_accessible():
                domain.accessed_now()

                if not self.dic_url_per_domain[domain]:
                    del self.dic_url_per_domain[domain]

                url, depth = url_list[0]
                url_list.pop(0)
                return url, depth

        time.sleep(self.TIME_LIMIT_BETWEEN_REQUESTS)

        return None, None


    def can_fetch_page(self,obj_url):
        """
        Verifica, por meio do robots.txt se uma determinada URL pode ser coletada
        """
        robot = urllib.robotparser.RobotFileParser()
        robot.set_url(obj_url.geturl())

        if obj_url.netloc not in self.dic_robots_per_domain:
            self.dic_robots_per_domain[obj_url.netloc] = robot.read()
            return robot.can_fetch(self.str_usr_agent, obj_url.geturl())

        return False

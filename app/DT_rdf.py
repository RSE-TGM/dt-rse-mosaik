import datetime

from rdflib import Graph, Namespace, Literal, URIRef
import uuid



def rdfcreate(namespace="http://tgm-sda.rse-web.it/",indexpath="DTindex.json", name="MinioFolder1", description="Questa è una descrizione"):
        g = Graph()
        # add title to ontology
        sda = Namespace(namespace)
        g.bind("sda", sda)
    
        # create config URI
        new_config = sda[f'DTSDA_{str(uuid.uuid4())}']

        g.add((new_config, sda["name"], Literal(name)))
        g.add((new_config, sda["description"], Literal(description)))
        g.add((new_config, sda["date"], Literal(f"{datetime.datetime.now()}")))
        g.serialize(indexpath, format="json-ld")

def rdfquery(namespace="http://tgm-sda.rse-web.it/",indexpath="DTindex.json") -> dict:
        # get Diagrams Point to be converted to Position Points
        g = Graph()
        g.parse( indexpath)
        sda = Namespace(namespace)
        
        query = """
        PREFIX tgm: <{sda}>
        SELECT  ?x ?name ?date ?desc
        WHERE {{ ?x 
        tgm:date ?date; 
        tgm:description ?desc; 
        tgm:name ?name.
        }}
        """.format(sda=sda)

        # self.query = """
        # PREFIX tgm: <{sda}>
        # SELECT  ?desc
        # WHERE {{ ?x tgm:description ?desc; 
        # }}
        # """.format(sda=self.sda)

        if rdf_debug: 
             print(query)

        # Query the graph
        results = g.query(query)
        
        if rdf_debug:
             for row in results:
                print(row)

        for row in results:
            name = str(row.asdict()['name'].toPython())
            if rdf_debug: print(f"name = {name}")
            desc = str(row.asdict()['desc'].toPython())
            if rdf_debug: print(f"desc = {desc}")
            date = str(row.asdict()['date'].toPython())
            if rdf_debug: print(f"date = {date}")

        return {'name':name, 'description':desc, 'date':date }


def rdfTest():
    rdfcreate(name="Config1", description=" Configurazione n. 1")
    rdfquery(indexpath="index.json")

    rdfcreate(name="Config_2", description=" Configurazione n. 2")
    outdict= rdfquery(indexpath="index.json")
    print(outdict)
    return ("ecco:", outdict)

if __name__ == '__main__':
    NAMESPACEDEF="http://tgm-sda.rse-web.it/"
    rdf_debug=True
    rdfTest()
else:
    rdf_debug=False


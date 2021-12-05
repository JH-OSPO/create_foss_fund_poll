import requests
import os
import ldap
import jsonpickle
import json
import subprocess
import datetime

token = os.environ['GITHUB_TOKEN']
headers = {"Authorization": f"Bearer {token}"}
ldap_password = os.environ['JHED_PASSWORD']
ldap_username = os.environ['JHED_ID']
github_slug = os.getenv(['GH_SLUG'], default="johns-hopkins-university")

starfish_input = "starfish_input.csv"

class GitHubUser(object):
    login = None
    own_repositories = []
    organizations = []
    
    
class JHEDUser(object):
    jhed_id = None
    givenName = None
    surName = None
    displayName = None
    role = None
    group = None
    title = None
    mail = None
    department = None
    cached_date = None
    
class User(GitHubUser, JHEDUser):
    def __init__(self):
        self.login = ''
        self.jhed_id = ''
        self.givenName = ''
        self.surName = ''
        self.displayName = ''
        self.role = ''
        self.group = ''
        self.title = ''
        self.mail = ''
        self.department = ''


    def gh_populate(self, blob):
        self.jhed_id = blob['jhed_id'].split('@')[0]
        self.login = blob['gh_login']

    def get_jhed(self):
        l = ldap.initialize('ldaps://ldap.johnshopkins.edu:636', bytes_mode=False)
        username = "cn={0},ou=people,dc=win,dc=ad,dc=jhu,dc=edu".format(ldap_username)
        try:
            l.protocol_version = ldap.VERSION3
            l.simple_bind_s(username, ldap_password)
            valid = True

            r = l.search_s('ou=people,dc=win,dc=ad,dc=jhu,dc=edu', ldap.SCOPE_SUBTREE, '(cn={0})'.format(self.jhed_id))

            obj = r[0][1]
            self.givenName = str(obj['givenName'][0], 'ASCII')
            self.surName = str(obj['sn'][0], 'ASCII')
            self.displayName = str(obj['displayName'][0], 'ASCII')
            self.role = str(obj['eduPersonAffiliation'][0], 'ASCII')
            self.group = str(obj['ou'][0], 'ASCII')
            self.title = str(obj['title'][0], 'ASCII')
            self.mail = str(obj['mail'][0], 'ASCII')
            self.department = str(obj['eduPersonOrgUnitDn'][0], 'ASCII')

        except Exception as error:
            print(error)
            exit
        
    def __repr__(self):
        return f''' 
JHED Id: {self.jhed_id}
GitHub Login: {self.login}
Name: {self.displayName}
Mail: {self.mail}
Title: {self.title}
Role: {self.role}
Department: {self.department}
Group: {self.group}'''


class Enterprise(object):
    members = None
    last_cached = None

    def __init__(self):
        self.last_cached = datetime.datetime.now()
        self.members = []

def run_query(query, variables):
    request = requests.post('https://api.github.com/graphql', json={'query': query, 'variables': variables}, headers=headers)

    if request.status_code == 200:
        return request.json()
    else:
        raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query))

def get_samlidentities(slug, cursor=None):
    identities = []
    hasNext = True
    query = '''
        query FetchSAMLIdentities($slug: String!, $cursor: String) {
          enterprise(slug: $slug) {
            ownerInfo {
              samlIdentityProvider {
                externalIdentities(first: 50, after: $cursor) {
                  nodes {
                    samlIdentity {
                      username
                      nameId
                    }
                    user {
                      login
                    }
                  }
                  pageInfo {
                    endCursor
                    hasNextPage
                  }
                }
              }
            }
          }
        }
    '''

    while hasNext:
        params = {
            'slug': slug,
            'cursor': cursor
        }

        result = run_query(query, params)
        for identity in result['data']['enterprise']['ownerInfo']['samlIdentityProvider']['externalIdentities']['nodes']:
            if identity['user'] is not None:
                print(f"Processing {identity['samlIdentity']['username']}")
                i = { 'jhed_id': identity['samlIdentity']['username'], 'gh_login': identity['user']['login'] }
                user = User()
                user.gh_populate(i)
                user.get_jhed()
                
                identities.append(user)
        hasNext = result['data']['enterprise']['ownerInfo']['samlIdentityProvider']['externalIdentities']['pageInfo']['hasNextPage']
        cursor = result['data']['enterprise']['ownerInfo']['samlIdentityProvider']['externalIdentities']['pageInfo']['endCursor']

    return identities

def generate_starfish_input_csv(enterprise):
    with open(starfish_input, 'w') as i:
        i.write("My GitHub Id is:,EMAIL\n")
        for member in enterprise.members:
            i.write(f"{member.login},{member.mail}\n")

def generate_cache():
    print("Generating new cache")
    enterprise_new = Enterprise()
    enterprise_new.members = get_samlidentities()

    return enterprise_new

try:
    contents = ''
    enterprise = None
    if os.path.exists("cached_data.json"):
        with open("cached_data.json", 'r') as file:
            contents = file.read()

            enterprise = jsonpickle.decode(contents)

    cache_limit = datetime.datetime.now() - datetime.timedelta(hours=3)

    if enterprise is None or enterprise.last_cached < cache_limit:
        enterprise = generate_cache()
        pickled = jsonpickle.encode(enterprise)

        with open("cached_data.json", "w") as file:
            file.write(pickled)
    
        enterprise = enterprise

    print(enterprise)
    generate_starfish_input_csv(enterprise)

    #p = subprocess.Popen(["/usr/bin/node", "index.js", "../starfish_input.csv", f"{(datetime.datetime.now() - datetime.timedelta(weeks=52)).isoformat()}", f"{datetime.datetime.now().isoformat()}"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, cwd="starfish", text=True)
    #stdout,stderr = p.communicate()

    #os.remove(starfish_input)
    #voters = stdout.split("\n")[4:]
    #for email in voters:
    #    print(email)

        
except Exception as e:
    print(e)

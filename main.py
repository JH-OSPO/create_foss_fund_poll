import requests
import os
import ldap

token = os.environ['GITHUB_TOKEN']
headers = {"Authorization": f"Bearer {token}"}
ldap_password = os.environ['JHED_PASSWORD']
ldap_username = os.environ['JHED_ID']

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
    
class User(GitHubUser, JHEDUser):
    def init(self):
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


def get_jhed_user(user):

    l = ldap.initialize('ldaps://ldap.johnshopkins.edu:636', bytes_mode=False)
    username = "cn={0},ou=people,dc=win,dc=ad,dc=jhu,dc=edu".format(ldap_username)
    try:
        l.protocol_version = ldap.VERSION3
        l.simple_bind_s(username, ldap_password)
        valid = True

        r = l.search_s('ou=people,dc=win,dc=ad,dc=jhu,dc=edu', ldap.SCOPE_SUBTREE, '(cn={0})'.format(user.jhed_id))

        obj = r[0][1]
        user.givenName = str(obj['givenName'][0], 'ASCII')
        user.surName = str(obj['sn'][0], 'ASCII')
        user.displayName = str(obj['displayName'][0], 'ASCII')
        user.role = str(obj['eduPersonAffiliation'][0], 'ASCII')
        user.group = str(obj['ou'][0], 'ASCII')
        user.title = str(obj['title'][0], 'ASCII')
        user.mail = str(obj['mail'][0], 'ASCII')
        user.department = str(obj['eduPersonOrgUnitDn'][0], 'ASCII')

        return user

    except Exception as error:
        print(error)
        exit
    
def run_query(query, variables):
    request = requests.post('https://api.github.com/graphql', json={'query': query, 'variables': variables}, headers=headers)

    if request.status_code == 200:
#        print(request.json())
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
                i = { 'jhed_id': identity['samlIdentity']['username'], 'gh_login': identity['user']['login'] }
                identities.append(i)
        hasNext = result['data']['enterprise']['ownerInfo']['samlIdentityProvider']['externalIdentities']['pageInfo']['hasNextPage']
        cursor = result['data']['enterprise']['ownerInfo']['samlIdentityProvider']['externalIdentities']['pageInfo']['endCursor']

    return identities

for ident in get_samlidentities("johns-hopkins-university"):
    user = User()
    user.gh_populate(ident)

    user = get_jhed_user(user)
    print(user)

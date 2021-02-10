import requests
import os

token = os.environ['GITHUB_TOKEN']
headers = {"Authorization": f"Bearer {token}"}

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

print("My GitHub ID is:,JHED ID")
for ident in get_samlidentities("johns-hopkins-university"):
    print(f"{ident['gh_login']},{ident['jhed_id']}")

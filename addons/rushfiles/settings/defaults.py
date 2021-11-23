# Drive credentials
CLIENT_ID = 'changeme'
CLIENT_SECRET = 'changeme'

EXPIRY_TIME = 60 * 60 * 24 * 60  # 60 days
REFRESH_TIME = 60 * 60 * 12  # 12 hours (token is valid for 24 hours)

OAUTH_SCOPE = ['openid', 'profile', 'domain_api', 'offline_access']
OAUTH_BASE_URL = 'https://auth.rushfiles.com/connect/'

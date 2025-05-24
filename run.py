from app import app, db
from app.models.user import User, InviteCode
from app.models.prompt import Prompt, Tag

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db, 
        'User': User, 
        'InviteCode': InviteCode,
        'Prompt': Prompt,
        'Tag': Tag
    }

if __name__ == '__main__':
    app.run(debug=True) 
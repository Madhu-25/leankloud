from flask import Flask
from flask import jsonify , make_response
from flask.globals import request
from flask_restplus import Api, Resource, fields
import re
import datetime
from functools import wraps
from werkzeug.contrib.fixers import ProxyFix

'''
from enum import Enum, EnumMeta
class LoginState(EnumMeta):
    INVALID = True
    READONLY = False
    WRITEACCESS = False'''




import MySQLdb

db = MySQLdb.connect(host="localhost",    # your host, usually localhost
                     user="root",         # your username
                     passwd="madhu",  # your password
                     db="todo",
                     port=3307)        # name of the data base

# you must create a Cursor object. It will let
#  you execute all the queries you need
cur = db.cursor()


app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)
app.config['PROPAGATE_EXCEPTIONS'] = True

authorizations = {
    'apikey' : {
        'type' : 'apiKey',
        'in' : 'header',
        'name' : 'X-API-KEY'
    }
}



#wsgi_app -> used so that middlewares can be applied without losing a reference to the app object. 

#ProxyFix -> This middleware is applied to add HTTP proxy support to an application 
api = Api(app, version='1.0', title='TodoMVC API',
    description='A simple TodoMVC API', authorizations=authorizations
)


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        print(request.headers)
        if 'X-API-KEY' in request.headers:
            
            token = request.headers['X-API-KEY']
        if not token:
            api.abort(401,'token is missing.')

        if token != 'canwrite' and token!= 'readonly':
            api.abort(401, 'You are not authorized to access the api')
        
        print('TOKEN: {}'.format(token))
        return f(*args, **kwargs)

    return decorated


def write_token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'X-API-KEY' in request.headers:
            token = request.headers['X-API-KEY']
        if not token:
            api.abort(401,'token is missing.')

        if token != 'canwrite' and token!= 'readonly':
            api.abort(401, 'You are not authorized to access the api')
            
        
        if token != 'canwrite':
            api.abort(401,'You are not authorized to write' )
            
        
        print('TOKEN: {}'.format(token))
        return f(*args, **kwargs)

    return decorated




ns = api.namespace('todos', description='TODO operations')

todo = api.model('Todo', {
    
    'id': fields.Integer(readonly=True, description='The task unique identifier'),
    'task': fields.String(required=True, description='The task details'),
    'due_date' : fields.Date(required=True, description='deadline in yyyy-mm-dd format'),
    'status' : fields.String(required=True, description='work status enter any one of the following: \'not started\', \'finished\', \'in progress\''),
    
})
'''
user = api.model('User', {
        'user_id': fields.String(required=True, description='Email id'),
    'password': fields.String(required=True, description='Password'),
    'message' : fields.String(readonly=True, description='login message')

})
'''


def get_object(todo):
    tasks = []
    for each in todo:
        task = dict()
        task['id'] = each[0]
        task['task'] = each[1]
        task['due_date'] = each[2]
        task['status'] = each[3]
        
        tasks.append(task)
    return tasks

def get_id(id):
    cur.execute('SELECT * FROM  TODOLIST WHERE ID ='+str(id))
    todo = cur.fetchall()
    
    
    if(cur.rowcount==0):
        api.abort(404, "Todo {} doesn't exist".format(id))
        return
    todo = todo[0]
    task = dict()
    task['id'] = todo[0]
    task['task'] = todo[1]
    task['due_date'] = todo[2]
    task['status'] = todo[3]
    
    return task
        

def create(data):
   
    due = data['due_date']
    x = re.search("[0-9]{4}-[0-9]{2}-[0-9]{2}", due)
    if(x == None):
        api.abort(404, "Enter Due date in yyyy-mm-dd format")
        return
    if(data['status']!="not started" and data['status']!="finished" and data['status']!="in progress"):
        api.abort(404, "work status enter any one of the following: 'not started', 'finished', 'in progress'")
        return
    cur.execute('SELECT * FROM ids')
    counter = cur.fetchall() 
    counter= counter[0][0] +1
    print('inserting id: ',counter)
    cur.execute('UPDATE IDS SET ID'+'='+str(counter))
    db.commit()
    sql ='INSERT INTO TODOLIST VALUES (%s, %s, %s, %s)'
    val =(str(counter), data['task'], data['due_date'], data['status'])
    cur.execute(sql,val)
    db.commit()
    print(cur.rowcount)
    cur.execute('SELECT * FROM TODOLIST')
    todo = cur.fetchall()
    tasks = get_object(todo)

    return tasks

def get_date(date):
    
    cur.execute('SELECT * FROM  TODOLIST WHERE DUE_DATE = \''+ date + '\'')
    todo = cur.fetchall()
    if(cur.rowcount == 0):
        api.abort(404, "Todo with due date {} doesn't exist".format(date))
        return
    tasks =[]
    for each in todo:
        if(each[2]!=date):
            continue
        task = dict()
        task['id'] = each[0]
        task['task'] = each[1]
        task['due_date'] = each[2]
        task['status'] = each[3]
        tasks.append(task)
        

    return tasks



def get_todo():
    
    cur.execute('SELECT * FROM TODOLIST')
    todo = cur.fetchall()
    tasks = get_object(todo)
    return tasks

def get_overdue():
    
    cur.execute('SELECT * FROM TODOLIST')
    todo = cur.fetchall()
    tasks =[]
    today = datetime.datetime.now()
    date = str(today.date())
    for each in todo:
        if(each[2]<=date and each[3]!="finished"):
            task = dict()
            task['id'] = each[0]
            task['task'] = each[1]
            task['due_date'] = each[2]
            task['status'] = each[3]
            tasks.append(task)
    if(tasks):
        return tasks
    else:
        api.abort(404, "No work overdue")
        return


def get_finished():
    
    cur.execute('SELECT * FROM TODOLIST')
    todo = cur.fetchall()
    tasks =[]
    for each in todo:
        if(each[3]=="finished"):
            task = dict()
            task['id'] = each[0]
            task['task'] = each[1]
            task['due_date'] = each[2]
            task['status'] = each[3]
            tasks.append(task)
    
    if(tasks):
        return tasks
    else:
        api.abort(404, "No work has been completed yet")
        return


def delete_id(id):
    cur.execute('SELECT * FROM  TODOLIST WHERE ID ='+str(id))
    
    if(cur.rowcount==0):
        api.abort(404, "Todo {} doesn't exist".format(id))
        return
    cur.execute('DELETE FROM TODOLIST WHERE ID = '+str(id))
    db.commit()
    cur.execute('SELECT * FROM TODOLIST')
    todo = cur.fetchall()
    tasks =get_object(todo)
    return tasks
    

def update(data, id):
    cur.execute('SELECT * FROM  TODOLIST WHERE ID ='+str(id))
    print(data)
    if(cur.rowcount==0):
        api.abort(404, "Todo {} doesn't exist".format(id))
        return
    due = data['due_date']
    x = re.search("[0-9]{4}-[0-9]{2}-[0-9]{2}", due)
    if(x == None):
        api.abort(404, "Enter Due date in yyyy-mm-dd format")
        return
    if(data['status']!="not started" and data['status']!="finished" and data['status']!="in progress"):
        api.abort(404, "work status enter any one of the following: 'not started', 'finished', 'in progress'")
        return
    cur.execute('UPDATE TODOLIST SET TASK'+'=\''+str(data['task'])+'\', DUE_DATE=\''+str(data['due_date'])+'\', FINISHED=\''+str(data['status'])+'\' WHERE ID='+str(id)+';')
    db.commit()
    cur.execute('SELECT * FROM TODOLIST')
    todo = cur.fetchall()
    print(todo)
    tasks = get_object(todo)
    
    return tasks


'''def login(data):
   
    res['user_id'] = data['user_id']
    res['password'] = '*hidden*'
    cur.execute('SELECT * FROM USERS WHERE EMAIL'+'=\''+str(data['user_id'])+'\'')
    row = cur.fetchall()
    print(row)
    if(row):
        if(row[0][1]==data['password']):
            if(row[0][2]==1):
                LoginState.WRITEACCESS = True
                LoginState.READONLY = False
                LoginState.INVALID=False
                res['message'] = 'Write access user logged in....'
                return res
                
            else:
                LoginState.WRITEACCESS = False
                LoginState.READONLY = True
                LoginState.INVALID = False
               
                res['message'] = 'Readonly access user logged in...'
                return res
                
    
    LoginState.WRITEACCESS = False
    LoginState.READONLY = False
    LoginState.INVALID = True
    res['message'] = 'invalid login...'
    return res
        
    
        
def logout():
    LoginState.WRITEACCESS = False
    LoginState.READONLY = False
    LoginState.INVALID = True
    res = dict()
    res['user_id'] = None
    res['password'] = None
    res['message'] = 'You are currently logged out...'
    return res

'''


'''@ns.route('/login')
class UserLogin(Resource):
    @ns.doc('login')
    @ns.expect(user)
    @ns.marshal_with(user)
    
    def post(self):
        sample = login(api.payload)
        print(sample)
        return sample 

@ns.route('/logout')
class UserLogout(Resource):
    @ns.doc('logout')
    @ns.marshal_with(user)
    def get(self):
        return logout()'''

@ns.route('/')
class TodoList(Resource):
    '''Shows a list of all todos, and lets you POST to add new tasks'''
    @ns.doc('list_todos')
    @ns.marshal_list_with(todo)
    @ns.doc(security = 'apikey')
    @token_required
    def get(self):
        '''List all tasks'''
        return get_todo()

    @ns.doc('create_todo')
    @ns.expect(todo)
    @ns.marshal_with(todo, code=201)
    @ns.doc(security = 'apikey')
    @write_token_required
    def post(self):
        '''Create a new task'''
        return create(api.payload), 201

@ns.route('/due/<string:due_date>')
@ns.response(404, 'Todo not found')
@ns.param('due_date', 'Deadline')
class Todo(Resource):
    @ns.doc('get_todo')
    @ns.marshal_with(todo)
    @ns.doc(security = 'apikey')
    @token_required
    def get(self, due_date):
        return get_date(due_date)


@ns.route('/overdue')
class Todo(Resource):
    @ns.doc('get_todo')
    @ns.marshal_with(todo)
    @ns.doc(security = 'apikey')
    @token_required
    def get(self):
        return get_overdue()


@ns.route('/finished')
class Todo(Resource):
    @ns.doc('get_todo')
    @ns.marshal_with(todo)
    @ns.doc(security = 'apikey')
    @token_required
    def get(self):
        return get_finished()



@ns.route('/<int:id>')
@ns.response(404, 'Todo not found')
@ns.param('id', 'The task identifier')
class Todo(Resource):
    '''Show a single todo item and lets you delete them'''
    @ns.doc('get_todo')
    @ns.marshal_with(todo)
    @ns.doc(security = 'apikey')
    @token_required
    def get(self, id):
        '''Fetch a given resource'''
        return get_id(id)

    @ns.doc('delete_todo')
    @ns.response(204, 'Todo deleted')
    @ns.doc(security = 'apikey')
    @write_token_required
    def delete(self, id):
        '''Delete a task given its identifier'''
        return delete_id(id)
        

    @ns.expect(todo)
    @ns.marshal_with(todo)
    @ns.doc(security = 'apikey')
    @write_token_required
    def put(self, id):
        '''Update a task given its identifier'''
        return update(api.payload, id)
        
        


if __name__ == '__main__':

    
    app.run(debug=True)

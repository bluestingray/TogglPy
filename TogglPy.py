# --------------------------------------------------------------
# TogglPy is a non-cluttered, easily understood and implemented
# library for interacting with the Toggl API.
# --------------------------------------------------------------
from datetime import datetime
# for making requests
import urllib2
import urllib

# parsing json data
import json


#
# ---------------------------------------------
# Class containing the endpoint URLs for Toggl
# ---------------------------------------------
class Endpoints():
    WORKSPACES = "https://www.toggl.com/api/v8/workspaces"
    CLIENTS = "https://www.toggl.com/api/v8/clients"
    PROJECTS = "https://www.toggl.com/api/v8/projects"
    TASKS = "https://www.toggl.com/api/v8/tasks"
    REPORT_WEEKLY = "https://toggl.com/reports/api/v2/weekly"
    REPORT_DETAILED = "https://toggl.com/reports/api/v2/details"
    REPORT_SUMMARY = "https://toggl.com/reports/api/v2/summary"
    START_TIME = "https://www.toggl.com/api/v8/time_entries/start"
    TIME_ENTRIES = "https://www.toggl.com/api/v8/time_entries"
    SIGNUPS = "https://www.toggl.com/api/v8/signups"
    MY_USER = "https://www.toggl.com/api/v8/me"

    @staticmethod
    def STOP_TIME(pid):
        return "https://www.toggl.com/api/v8/time_entries/" + str(pid) + "/stop"

    CURRENT_RUNNING_TIME = "https://www.toggl.com/api/v8/time_entries/current"


# -------------------------------------------------------
# Class containing the necessities for Toggl interaction
# -------------------------------------------------------
class Toggl():
    # template of headers for our request
    headers = {
        "Authorization": "",
        "Content-Type": "application/json",
        "Accept": "*/*",
        "User-Agent": "python/urllib",
    }

    # default API user agent value
    user_agent = "TogglPy"

    # -------------------------------------------------------------
    # Auxiliary methods
    # -------------------------------------------------------------

    def decodeJSON(self, jsonString):
        return json.JSONDecoder().decode(jsonString)

    # -------------------------------------------------------------
    # Methods that modify the headers to control our HTTP requests
    # -------------------------------------------------------------
    def setAPIKey(self, APIKey):
        '''set the API key in the request header'''
        # craft the Authorization
        authHeader = APIKey + ":" + "api_token"
        authHeader = "Basic " + authHeader.encode("base64").rstrip()

        # add it into the header
        self.headers['Authorization'] = authHeader

    def setAuthCredentials(self, email, password):
        authHeader = '{0}:{1}'.format(email, password)
        authHeader = "Basic " + authHeader.encode("base64").rstrip()

        # add it into the header
        self.headers['Authorization'] = authHeader

    def setUserAgent(self, agent):
        '''set the User-Agent setting, by default it's set to TogglPy'''
        self.user_agent = agent

    # ------------------------------------------------------
    # Methods for directly requesting data from an endpoint
    # ------------------------------------------------------

    def requestRaw(self, endpoint, parameters=None):
        '''make a request to the toggle api at a certain endpoint and return the RAW page data (usually JSON)'''
        if parameters == None:
            return urllib2.urlopen(urllib2.Request(endpoint, headers=self.headers)).read()
        else:
            if 'user_agent' not in parameters:
                parameters.update({'user_agent': self.user_agent, })  # add our class-level user agent in there
            endpoint = endpoint + "?" + urllib.urlencode(parameters)  # encode all of our data for a get request & modify the URL
            return urllib2.urlopen(urllib2.Request(endpoint, headers=self.headers)).read()  # make request and read the response

    def request(self, endpoint, parameters=None):
        '''make a request to the toggle api at a certain endpoint and return the page data as a parsed JSON dict'''
        return json.loads(self.requestRaw(endpoint, parameters))

    def postRequest(self, endpoint, parameters=None):
        '''make a POST request to the toggle api at a certain endpoint and return the RAW page data (usually JSON)'''
        if parameters == None:
            return json.loads(urllib2.urlopen(urllib2.Request(endpoint, headers=self.headers)).read())
        else:
            data = json.JSONEncoder().encode(parameters)
            return json.loads(urllib2.urlopen(urllib2.Request(endpoint, data=data, headers=self.headers)).read())  # make request and read the response

    def putRequest(self, endpoint, parameters=None):
        '''make a POST request to the toggle api at a certain endpoint and return the RAW page data (usually JSON)'''
        if parameters == None:
            request = urllib2.Request(endpoint, headers=self.headers)
            request.get_method = lambda: 'PUT'
            return json.loads(urllib2.urlopen(request).read())
        else:
            data = json.JSONEncoder().encode(parameters)
            request = urllib2.Request(endpoint, data=data, headers=self.headers)
            request.get_method = lambda: 'PUT'
            return json.loads(urllib2.urlopen(request).read())  # make request and read the response

    # ----------------------------------
    # Methods for managing Time Entries
    # ----------------------------------

    def startTimeEntry(self, description, pid):
        '''starts a new Time Entry'''
        data = {
            "time_entry": {
                "description": description,
                "pid": pid,
                "created_with": self.user_agent
            }
        }
        response = self.postRequest(Endpoints.START_TIME, parameters=data)
        return self.decodeJSON(response)

    def currentRunningTimeEntry(self):
        '''Gets the Current Time Entry'''
        response = self.postRequest(Endpoints.CURRENT_RUNNING_TIME)
        return self.decodeJSON(response)

    def stopTimeEntry(self, entryid):
        '''Stop the time entry'''
        response = self.postRequest(Endpoints.STOP_TIME(entryid))
        return self.decodeJSON(response)

    def createTimeEntry(self, hourduration, projectid=None, projectname=None,
                        clientname=None, year=None, month=None, day=None, hour=None):
        """
        Creating a custom time entry, minimum must is hour duration and project param
        :param hourduration:
        :param projectid: Not required if projectname given
        :param projectname: Not required if projectid was given
        :param clientname: Can speed up project query process
        :param year: Taken from now() if not provided
        :param month: Taken from now() if not provided
        :param day: Taken from now() if not provided
        :param hour: Taken from now() if not provided
        :return: response object from post call
        """
        data = {
            "time_entry": {}
        }

        if not projectid:
            if projectname and clientname:
                projectid = (self.getClientProject(clientname, projectname))['data']['id']
            elif projectname:
                projectid = (self.searchClientProject(projectname))['data']['id']
            else:
                print 'Too many missing parameters for query'
                exit(1)

        year = datetime.now().year if not year else year
        month = datetime.now().month if not month else month
        day = datetime.now().day if not day else day
        hour = datetime.now().hour if not hour else hour

        timestruct = datetime(year, month, day, hour - 2).isoformat() + '.000Z'
        data['time_entry']['start'] = timestruct
        data['time_entry']['duration'] = hourduration * 3600
        data['time_entry']['pid'] = projectid
        data['time_entry']['created_with'] = 'NAME'

        response = self.postRequest(Endpoints.TIME_ENTRIES, parameters=data)
        return self.decodeJSON(response)

    # -----------------------------------
    # Methods for getting workspace data
    # -----------------------------------
    def getWorkspaces(self):
        '''return all the workspaces for a user'''
        return self.request(Endpoints.WORKSPACES)

    def getWorkspace(self, name=None, id=None):
        '''return the first workspace that matches a given name or id'''
        workspaces = self.getWorkspaces()  # get all workspaces

        # if they give us nothing let them know we're not returning anything
        if name == None and id == None:
            print "Error in getWorkspace(), please enter either a name or an id as a filter"
            return None

        if id == None:  # then we search by name
            for workspace in workspaces:  # search through them for one matching the name provided
                if workspace['name'] == name:
                    return workspace  # if we find it return it
            return None  # if we get to here and haven't found it return None
        else:  # otherwise search by id
            for workspace in workspaces:  # search through them for one matching the id provided
                if workspace['id'] == int(id):
                    return workspace  # if we find it return it
            return None  # if we get to here and haven't found it return None

    def getWorkspaceUsers(self, workspace_id):
        """
        :param workspace_id: Workspace ID by which to query
        :return: Users object returned from endpoint request
        """
        return self.request(Endpoints.WORKSPACES + '/{0}/workspace_users'.format(workspace_id))

    def getWorkspaceClients(self, workspace_id):
        """
        :param workspace_id: Workspace ID by which to query
        :return: Clients object returned from endpoint request
        """
        return self.request(Endpoints.WORKSPACES + '/{0}/clients'.format(workspace_id))

    def getWorkspaceTasks(self, workspace_id, active='true'):
        return self.request(Endpoints.WORKSPACES + '/{0}/tasks'.format(workspace_id), parameters={'active': active})

    def createUser(self, data):
        """
        :param data: Dictionary of data to create the user
        :return: Users object returned from endpoint request
        """
        return self.postRequest(Endpoints.SIGNUPS, parameters={'user': data})

    def myUser(self):
        """
        :return: Users object returned from endpoint request
        """
        return self.request(Endpoints.MY_USER)

    # --------------------------------
    # Methods for getting client data
    # --------------------------------
    def getClients(self):
        '''return all clients that are visable to a user'''
        return self.request(Endpoints.CLIENTS)

    def getClient(self, name=None, id=None):
        '''return the first client that matches a given name or id'''
        clients = self.getClients()  # get all clients

        # if they give us nothing let them know we're not returning anything
        if name == None and id == None:
            print "Error in getClient(), please enter either a name or an id as a filter"
            return None

        if id == None:  # then we search by name
            for client in clients:  # search through them for one matching the name provided
                if client['name'] == name:
                    return client  # if we find it return it
            return None  # if we get to here and haven't found it return None
        else:  # otherwise search by id
            for client in clients:  # search through them for one matching the id provided
                if str(client['id']) == str(id):
                    return client  # if we find it return it
            return None  # if we get to here and haven't found it return None

    def createClient(self, data):
        """
        :param data: Dictionary of data to create the client
        :return: Client object returned from endpoint request
        """
        return self.postRequest(Endpoints.CLIENTS, parameters={'client': data})

    def updateClient(self, id, data):
        """
        :param id: Client id by which to query
        :param data: Dictionary of data to update the client
        """
        return self.putRequest(Endpoints.CLIENTS + '/{}'.format(id), parameters={'client': data})

    def getClientProjects(self, id):
        """
        :param id: Client ID by which to query
        :return: Projects object returned from endpoint
        """
        return self.request(Endpoints.CLIENTS + '/{0}/projects'.format(id))

    def searchClientProject(self, name):
        """
        Provide only a projects name for query and search through entire available names
        WARNING: Takes a long time!
                 If client name is known, 'getClientProject' would be advised
        :param name: Desired Project's name
        :return: Project object
        """
        for client in self.getClients():
            try:
                for project in self.getClientProjects(client['id']):
                    if project['name'] == name:
                        return project
            except:
                continue

        print 'Could not find client by the name'
        return None

    def getClientProject(self, clientName, projectName):
        """
        Fast query given the Client's name and Project's name
        :param clientName:
        :param projectName:
        :return:
        """
        for client in self.getClients():
            if client['name'] == clientName:
                cid = client['id']

        if not cid:
            print 'Could not find such client name'
            return None

        for projct in self.getClientProjects(cid):
            if projct['name'] == projectName:
                pid = projct['id']

        if not pid:
            print 'Could not find such project name'
            return None

        return self.getProject(pid)

    # --------------------------------
    # Methods for getting PROJECTS data
    # --------------------------------
    def getProjects(self, workspace_id):
        return self.request(Endpoints.WORKSPACES + '/{0}/projects'.format(workspace_id))

    def getProject(self, workspace_id, name=None, id=None):
        projects = self.getProjects(workspace_id)

        if name is None and id is None:
            print "Error in getProject(), please enter either a name or an id as a filter"
            return None

        if id is None:
            for project in projects:
                if project['name'] == name:
                    return project
            return None
        else:
            for project in projects:
                if str(project['id']) == str(id):
                    return project
            return None

    def updateProject(self, id, data):
        return self.putRequest(Endpoints.PROJECTS + '/{0}'.format(id), parameters={'project': data})

    def createProject(self, data):
        return self.postRequest(Endpoints.PROJECTS, parameters={'project': data})

    def getProjectUsers(self, id):
        """
        :param id: Project ID by which to query
        :return: Users object returned from endpoint
        """
        return self.request(Endpoints.PROJECTS + '/{0}/project_users'.format(id))

    def getProjectTasks(self, project_id):
        """
        :param project_id: Project ID by which to query
        :return: Tasks object returned from endpoint
        """
        return self.request(Endpoints.PROJECTS + '/{0}/tasks'.format(project_id))

    def getTasks(self):
        return self.request(Endpoints.TASKS)

    def getTaskDetail(self, task_id):
        return self.request(Endpoints.TASKS + '/{0}'.format(task_id))

    def getTask(self, id=None, workspace_id=None, project_id=None, name=None):
        if name is None and id is None:
            return
        if name and workspace_id is None:
            return
        if name:
            name = name.encode('utf-8')

        # If there is no ID passed into this method then we are assuming
        # the user is trying to find the Toggl task based on the name
        # and project ID.
        if id is None:
            tasks = self.getWorkspaceTasks(workspace_id=workspace_id, active='both')
            if not tasks:
                return
            for task in tasks:
                task_name = task.get('name', '').encode('utf-8')
                if str(task_name) == str(name) and (not project_id or str(task['pid']) == str(project_id)):
                    return task

        # Otherwise we are going to try to use the id directly instead
        # of searching based off of a name.
        else:
            return self.getTaskDetail(task_id=id)

    def updateTask(self, task_id, data):
        """
        :param task_id:
        :param data:
        :return:
        """
        return self.putRequest(Endpoints.TASKS + '/{0}'.format(task_id), parameters={'task': data})

    def createTask(self, data):
        """
        :param data:
        :return:
        """
        return self.postRequest(Endpoints.TASKS, parameters={'task': data})

    # ---------------------------------
    # Methods for getting reports data
    # ---------------------------------
    def getWeeklyReport(self, data):
        '''return a weekly report for a user'''
        return self.request(Endpoints.REPORT_WEEKLY, parameters=data)

    def getWeeklyReportPDF(self, data, filename):
        '''save a weekly report as a PDF'''
        # get the raw pdf file data
        filedata = self.requestRaw(Endpoints.REPORT_WEEKLY + ".pdf", parameters=data)

        # write the data to a file
        with open(filename, "wb") as pdf:
            pdf.write(filedata)

    def getDetailedReport(self, data):
        '''return a detailed report for a user'''
        return self.request(Endpoints.REPORT_DETAILED, parameters=data)

    def getDetailedReportPDF(self, data, filename):
        '''save a detailed report as a pdf'''
        # get the raw pdf file data
        filedata = self.requestRaw(Endpoints.REPORT_DETAILED + ".pdf", parameters=data)

        # write the data to a file
        with open(filename, "wb") as pdf:
            pdf.write(filedata)

    def getSummaryReport(self, data):
        '''return a summary report for a user'''
        return self.request(Endpoints.REPORT_SUMMARY, parameters=data)

    def getSummaryReportPDF(self, data, filename):
        '''save a summary report as a pdf'''
        # get the raw pdf file data
        filedata = self.requestRaw(Endpoints.REPORT_SUMMARY + ".pdf", parameters=data)

        # write the data to a file
        with open(filename, "wb") as pdf:
            pdf.write(filedata)

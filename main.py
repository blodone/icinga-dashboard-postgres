from flask import Flask, request, render_template, jsonify
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_pyfile('config.py')
app.config.update(DEBUG=True)
app.config['SQLALCHEMY_DATABASE_URI'] = app.config['DATABASE_URL']
db = SQLAlchemy(app)


def service_query(state, hostgroup_id):

    if state == -1:
        query = "SELECT count(1) as count from icinga_services "
        query+=" RIGHT JOIN icinga_hostgroup_members USING (host_object_id)"
        query+=" WHERE icinga_hostgroup_members.hostgroup_id = '{}'".format(hostgroup_id)

    else:
        query = "SELECT count(1) as count from icinga_servicestatus "
        query+=" LEFT JOIN icinga_services USING (service_object_id)"
        query+=" RIGHT JOIN icinga_hostgroup_members USING (host_object_id)"
        query+=" WHERE last_hard_state = {}".format(state)
        query+=" AND icinga_hostgroup_members.hostgroup_id = '{}'".format(hostgroup_id)
    return query

@app.route('/', methods=['GET'])
def slash():
    d = {}
    d['refreshvalue'] = 60
    d['hostgroup'] = request.args.get('hostgroup', 'Ednic')
    con = db.engine.connect()
    query = "SELECT alias FROM icinga_hostgroups"
    r = con.execute(query)
    d['avail_hostgroups'] = r.fetchall()
    return render_template('index.html', **d)


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    d = {}
    d['hostgroup'] =  request.form.get('hostgroup')

    con = db.engine.connect()
    query = "SELECT hostgroup_id FROM icinga_hostgroups WHERE alias='{}'".format(d['hostgroup'])
    r = con.execute(query)
    try:
        d['selected_hostgroup_id'] = r.fetchall()[0][0]
    except IndexError:
        d['selected_hostgroup_id'] = 0

    """ hosts down """
    query = "SELECT icinga_hosts.display_name, icinga_hosts.alias from icinga_hosts "
    query+= " LEFT JOIN icinga_hoststatus USING (host_object_id)"
    query+= " RIGHT JOIN icinga_hostgroup_members USING (host_object_id)"
    query+= " WHERE icinga_hoststatus.last_hard_state = 1"
    query+= " AND icinga_hoststatus.problem_has_been_acknowledged = 0"
    query+= " AND icinga_hostgroup_members.hostgroup_id = '{}'".format(d['selected_hostgroup_id'])
    r = con.execute(query)
    d['hosts_down'] = r.fetchall()

    """ tactical hosts """
    query = "SELECT count(1) as count FROM icinga_hoststatus"
    query+= " RIGHT JOIN icinga_hostgroup_members USING (host_object_id)"
    query+= " WHERE last_hard_state=1"
    query+= " AND icinga_hostgroup_members.hostgroup_id='{}'".format(d['selected_hostgroup_id'])
    r = con.execute(query)
    d['hosts_down_count'] = r.fetchall()[0][0]

    query = "SELECT count(1) as count FROM icinga_hosts"
    query+= " RIGHT JOIN icinga_hostgroup_members USING (host_object_id)"
    query+= " WHERE icinga_hostgroup_members.hostgroup_id = '{}'".format(d['selected_hostgroup_id'])
    r = con.execute(query)
    d['hosts_total_count'] = r.fetchall()[0][0]
    if not d['hosts_total_count']:
        return render_template('dashboard.html', **d)

    d['hosts_down_pct'] = d['hosts_down_count'] / d['hosts_total_count'] * 100
    d['hosts_up_count'] = d['hosts_total_count'] - d['hosts_down_count']
    d['hosts_up_pct'] = d['hosts_up_count'] / d['hosts_total_count'] * 100

    """ tactical services """
    # total services count
    query = service_query(-1, d['selected_hostgroup_id'])
    r = con.execute(query)
    d['services_total_count'] = r.fetchall()[0][0]

    # up
    query = service_query(0, d['selected_hostgroup_id'])
    r = con.execute(query)
    d['services_up_count'] = r.fetchall()[0][0]

    # warning
    query = service_query(1, d['selected_hostgroup_id'])
    r = con.execute(query)
    d['services_warning_count'] = r.fetchall()[0][0]

    # down
    query = service_query(2, d['selected_hostgroup_id'])
    r = con.execute(query)
    d['services_down_count'] = r.fetchall()[0][0]

    # unknown
    query = service_query(3, d['selected_hostgroup_id'])
    r = con.execute(query)
    d['services_unknown_count'] = r.fetchall()[0][0]

    d['services_up_pct'] = round(float(d['services_up_count']) / float(d['services_total_count']) * 100, 2)
    d['services_warning_pct'] = round(float(d['services_warning_count']) / float(d['services_total_count']) * 100, 2)
    d['services_down_pct'] = round(float(d['services_down_count']) / float(d['services_total_count']) * 100, 2)
    d['services_unknown_pct'] = round(float(d['services_unknown_count']) / float(d['services_total_count']) * 100, 2)


    """ Services """
    query = "SELECT icinga_hosts.display_name,icinga_services.display_name,icinga_servicestatus.last_hard_state,icinga_servicestatus.output,icinga_servicestatus.last_hard_state_change,icinga_servicestatus.last_check"
    query+=" FROM icinga_servicestatus"
    query+=" LEFT JOIN icinga_services USING (service_object_id)"
    query+=" LEFT JOIN icinga_hosts USING (host_object_id)"
    query+=" LEFT JOIN icinga_hoststatus USING (host_object_id)"
    # hostgroup filter
    query+=" LEFT JOIN icinga_hostgroup_members USING (host_object_id)"
    query+=" WHERE icinga_servicestatus.last_hard_state in (1,2,3)"
    query+=" AND icinga_servicestatus.problem_has_been_acknowledged = 0"
    query+=" AND icinga_hoststatus.problem_has_been_acknowledged = 0"
    query+=" AND icinga_hoststatus.last_hard_state = 0"
    # only match selected hostgroup
    query+=" AND icinga_hostgroup_members.hostgroup_id = '{}'".format(d['selected_hostgroup_id'])
    query+=" ORDER BY icinga_servicestatus.last_hard_state DESC, icinga_hosts.display_name, icinga_services.display_name"

    r = con.execute(query)
    d['services'] = r.fetchall()

    """ render template """
    return render_template('dashboard.html', **d)


if __name__ == '__main__':
    app.run(debug=True)
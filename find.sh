###
#Creator Jabar Ali <jali@mirantis.com>


print_table()
{
 echo "---------------------------------------------"
 echo "DBNAME   :" $4
 echo "User     :" $1
 echo "passowrd :" $2
 echo "URL      :" $3
 echo "---------------------------------------------"
}

echo "CIDR-IPs"
echo "---------------------------------------------"
ifconfig|awk -F "[: ]+" '/inet addr:/ { if ($4 != "127.0.0.1") print $4 }'
echo "---------------------------------------------"

usr=`cat /etc/mysql/conf.d/password.cnf  | grep ^[^\#]|grep pass|cut -d"@" -f1`
my_sql_pass=`cat /etc/mysql/conf.d/password.cnf |grep ^[^\#] |grep pass|cut -d"@" -f1|cut -d"=" -f2`
url="----"
print_table "mysql:root" $my_sql_pass $url "MySql"

cat /etc/nova/nova.conf|grep ^[^\#] | grep conne.*mysql 
url=`cat /etc/nova/nova.conf|grep ^[^\#] | grep conne.*mysql` 
usr=`cat /etc/nova/nova.conf | grep ^[^\#] | grep conne.*mysql|cut -d"@" -f1|cut -d":" -f2` 
pass=`cat /etc/nova/nova.conf | grep ^[^\#]| grep conne.*mysql|cut -d"@" -f1|cut -d":" -f3` 

print_table $usr $pass $url "NOVA"

usr=`cat /etc/rabbitmq/rabbitmq.config|grep ^[^\#]|grep default_u|cut -d"," -f2`
pass=`cat /etc/rabbitmq/rabbitmq.config|grep ^[^\#]| grep  default_pa|cut -d"," -f2`
url="@"
print_table $usr $pass $url "RabbitMq"

url=`cat /etc/cinder/cinder.conf | grep conne.*mysql|cut -d":" -f3`
usr=`cat /etc/cinder/cinder.conf | grep conne.*mysql | cut -d"@" -f1 | cut -d":" -f2`
pass=`cat /etc/cinder/cinder.conf | grep conne.*mysql | cut -d"@" -f1 | cut -d":" -f3`

print_table $usr $pass $url "Cinder"

url=`cat /etc/glance/glance-api.conf | grep conne.*mysql | cut -d":" -f3`
usr=`cat /etc/glance/glance-api.conf | grep conne.*mysql|cut -d"@" -f1|cut -d":" -f2`
pass=`cat /etc/glance/glance-api.conf | grep conne.*mysql|cut -d"@" -f1|cut -d":" -f3`

print_table $usr $pass $url "Glance"

url=`cat  /etc/keystone/keystone.conf |grep conne.*mysql|cut -d":" -f3`
usr=`cat  /etc/keystone/keystone.conf |grep conne.*mysql|cut -d"@" -f1|cut -d":" -f2`
pass=`cat  /etc/keystone/keystone.conf |grep conne.*mysql|cut -d"@" -f1|cut -d":" -f3`

print_table $usr $pass $url "Keystone"

cat /etc/neutron/neutron.conf | grep ^[^\#]|grep conne.*mysql 
url=`cat /etc/neutron/neutron.conf | grep ^[^\#]|grep conne.*.mysq|cut -d":" -f3`
usr=`cat /etc/neutron/neutron.conf | grep ^[^\#]|grep conne.*.mysq|cut -d"@" -f1|cut -d":" -f2`
pass=`cat /etc/neutron/neutron.conf | grep ^[^\#]|grep conne.*.mysq|cut -d"@" -f1|cut -d":" -f3`

print_table $usr $pass $url "Neutron"



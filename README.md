# DB-Project-Basebook


1. sudo apt install python3-pip로 pip를 설치한다.
2. pip3 install flask로 flask 모듈을 설치한다.
3. sudo apt install mysql-server-5.7로 mysql을 설치한다.
4. mysql에서 database를 하나 원하는 이름으로 만들어준다. 
5. 그 다음에 dbtables.sql 파일이 있는 위치에서
mysql -u [user id] -p [password] [방금 생성한 DB명] < dbtables.sql
를 수행한다. 그러면 DB가 구축되었을 것이다.
6. app.py를 열어서 맨 위에 mysql 정보 4개를 입력한다. (user, password, name, host)
7. python3 app.py 를 하면 서버를 열 수 있다.

Redis Professional Services Consultant Technical Challenge
Hi Fahad J. Kiani,

Thank you for taking the time to complete this technical challenge!

Introduction
Objective: Demonstrate the building and synchronizing of Redis databases, and showcase your programming skills through the exercises below.


Exercise 1: Building and Synchronizing Redis Databases

Create a single-sharded Redis Enterprise database named source-db with no password, and a memory limit of 2GB. You can learn how to create Redis Enterprise databases here
Enable "Replica Of" by creating another single-sharded Redis Enterprise database named replica-db with no password and a memory limit of 2GB. Use source-db as the source database
On the load node, populate some data into source-db using memtier-benchmark. Put the contents of the command you ran in a file named /tmp/memtier_benchmark.txt on the load server
Write a small script/program using a language of your choice (e.g. Java, Python, Ruby, Go, Scala, C#, or JavaScript) to complete the following:
Insert the values 1-100 into the Redis database on source-db.
Read and print them in reverse order from replica-db.
In your documentation, discuss alternate Redis structures you can use to solve the problem and why you chose the solution you did

Exercise 2: Working with Redis REST API

REST API documentation for Redis can be found at here
REST API Endpoint is https://re-cluster1.ps-redislabs.org:9443. Please use the IP address if the host name isn't working.
Write a small script/program using a language of your choice (e.g. Java, Python, Ruby, Go, Scala, C#, or JavaScript) to complete the following:
Create a New Database: Utilize the Database API to create a new database without using any modules.
Create Three New Users: Utilize the Users API to add three new users to the system with the following details:
a. Email: john.doe@example.com, Name: John Doe, Role: db_viewer
b. Email: mike.smith@example.com, Name: Mike Smith, Role: db_member
c. Email: cary.johnson@example.com, Name: Cary Johnson, Role: admin
List and Display Users: Utilize the Users API to fetch and display all users in the specified format (name, role, and email).
Delete the Created Database: Database API to delete the previously created database.


Bonus Challenge: Working with Semantic Routers

Write an app in the language of your choice to do semantic routing (details below).
If you choose Python, you'll find much of the groundwork done for you in RedisVL. Follow the instructions in README.md to add RedisVL to your Python environment if that was your choice. Additional guidance is also found there.
In the provided cluster, create a single shard, single region db with Search and query enabled and any other features that you need. Use this new DB in your code. (For simplicity, you can allow unauthenticated data access as in the previous challenges.)
In your code, define three routes:
GenAI programming topics
Science fiction entertainment
Classical music
Write reasonable references and settings for each
The code must send requests to the best route
For this challenge, the route’s output only needs to show the name of the route

A little bit about this environment


There are 3 Redis Enterprise nodes with a cluster already configured between them: re-n1, re-n2, re-n3
You can access the Secure UI here
The credentials are admin@rl.org / n3Y2Cg9

There is a memtier_benchmark node you can use to load data. Access is described below

There is a bastion server that can be accessed here
To login, use the credentials term/n3Y2Cg9
Once logged in, su as root user (i.e. su)
Then su as labuser (i.e. su labuser)
SSH to either the RE nodes or the memtier_benchmark node
Redis Enteprise Nodes: ssh re-n1 (or re-n2, re-n3)
memtier_benchmark node: ssh load
You can now do rladmin, redis-cli, memtier_benchmark etc.
Note: You can sudo su on the Redis Enterprise nodes to enter root and terminate processes

You can access an VS Code IDE here. Password is n3Y2Cg9
If you prefer, you can use your own IDE and push to git
The IDE has git installed so you can clone and pull/save your code

You can use Redis Insight to browse the data in Redis. IGNORE THE UPDATE PROMPTS
You can get the database endpoint name from the Secure UI database configuration page. Please use the IP address if the host name isn't working.

Good luck! We are excited to see your innovative solution!


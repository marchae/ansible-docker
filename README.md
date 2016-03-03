### Description
Ansible playbook for building docker images

### Why
While docker containers is useful for various tasks process of their creation
leaves something to be desired:

1) RUN instructions in Dockerfile limited to simple commands

2) Poor reusability. You can't reuse RUN command from another Dockerfile
without inheriting from it or copying it

3) What if you want recreate docker image on bare metal, VM or some other
container runtime?

To solve this problems we could use existing provisioning tools such as Ansible
to build docker images.

### How
Run as
```
ansible-playbook --module-path=ansible/modules/docker ansible/site.yml
```

### Acknowledgement
Idea and initial implementation of caching plugin from article
[Provisioning Docker containers with Ansible][1] by [Xavier Bruhiere][2]

[1]: https://www.ibm.com/developerworks/cloud/library/cl-provision-docker-containers-ansible/
[2]: https://github.com/hackliff

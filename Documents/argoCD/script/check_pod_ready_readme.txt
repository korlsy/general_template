
example)

  1 #!/bin/sh
  2 minikube start \
  3 --driver=docker
  4
  5 ./check_pod_ready.sh argocd -c ./port_forward_argocd.sh
  6 echo "argocd ok!!"
  7 ./check_pod_ready.sh jenkins -c ./port_forward_jenkins.sh
  8 echo "jenkins ok!!"
  9
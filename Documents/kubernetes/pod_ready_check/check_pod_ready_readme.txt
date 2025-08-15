
example)

  1 #!/bin/sh
  2 minikube start \
  3 --driver=docker
  4
  5 ./sh/check_pod_ready.sh -n argocd -c ./sh/port_forward_argocd.sh
  6 echo "argocd ok!!"
  
  7 ./sh/check_pod_ready.sh -n jenkins -c ./sh/port_forward_jenkins.sh
  8 echo "jenkins ok!!"
  9
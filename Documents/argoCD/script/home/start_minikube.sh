#!/bin/sh
minikube start \
--driver=docker

./sh/check_pod_ready.sh -n argocd -c ./sh/port_forward_argocd.sh
echo "argocd ok!!"

#./sh/check_pod_ready.sh -n jenkins -c ./sh/port_forward_jenkins.sh
#echo "jenkins ok!!"



7-1. 쿠버네티스 Service 개념과 종류!
	kubectl describe svc clusterip-service 
	(서비스 상세 정보)
		nginx web home : /user/share/nginx/html/index.html
		kubectl scale deployment webui --replicas=5
		동적으로 변경되면 서비스도 변경 적용됨.
		( kubectl scale statefulset sf-nginx --replicas=4 )

7-2. 쿠버네티스 Service 4가지 종류 실습해보기
7-3. 쿠버네티스 Headless Service와 Kube Proxy 강좌

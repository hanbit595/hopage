# 작업 규칙

작업 전 docs/spec.md 와 docs/site-audit.md 를 읽고 그 기준을 따른다. 명세와 다르게 해야 하면 먼저 보고한다.
상위 폴더 D:\homepage 의 다른 폴더는 열지 않는다. 푸시는 승인 후에만 한다.
모든 보고·질문·커밋 메시지는 한국어로 쓴다.
예외: D:\homepage\docs\작업일지.md 는 맨 아래에 기록을 '추가'하는 것만 허용한다(기존 내용 수정·삭제 금지, 그 폴더의 다른 파일은 열지 않는다).
운영 반영 후에는 관리자 화면이 main 에 직접 저장한다. 개발은 admin-dev 에서 하고, 작업 시작 전 반드시 git merge origin/main 으로 관리자 저장분을 먼저 합친다.
main 에 직접 커밋하지 않는다(운영 반영은 admin-dev → main fast-forward 로만, 대표 승인 후).

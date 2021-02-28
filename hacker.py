import requests
import json
import sqlite3
import gi
import threading
from gi.repository import Gio
from time import sleep
from playsound import playsound

def notificaNovoAlvo(alvoInfo):

	Application = Gio.Application.new("hacker.one", Gio.ApplicationFlags.FLAGS_NONE)
	Application.register()

	Notification = Gio.Notification.new("Um novo alvo foi encontrado!")
	Notification.set_body(("A empresa/site " + alvoInfo['name'] + " aplicou para um programa no hackerone, corra atrás do bounty!"))

	Notification.set_icon(Gio.ThemedIcon.new("dialog-information"))

	Application.send_notification(None, Notification)

	playsound('notifica.mp3')

def verificaAlvo(cursorBanco, alvoId):

	cursorBanco.execute("SELECT name FROM hackerAlvos WHERE id = ?",(alvoId,))

	if cursorBanco.fetchone() == None:
		return True
	else:
		return False

def insereAlvo(cursorBanco, connBanco, alvoInfo):

	#https://stackoverflow.com/questions/14108162/python-sqlite3-insert-into-table-valuedictionary-goes-here/16698310
	columns = ', '.join(alvoInfo.keys())
	placeholders = ', '.join('?' * len(alvoInfo))

	sql = 'INSERT INTO hackerAlvos ({}) VALUES ({})'.format(columns, placeholders)

	values = [int(x) if isinstance(x, bool) else x for x in alvoInfo.values()]

	cursorBanco.execute(sql, values)

	connBanco.commit()

	return True

if __name__ == "__main__":

	session = requests.Session()
	conn = sqlite3.connect('infoResultados.db')
	c = conn.cursor()

	while True:
		headers = {'Content-Type':'application/json'}

		dataDirectory = """{"operationName":"DirectoryQuery","variables":{"where":{"_and":[{"_or":[{"submission_state":{"_eq":"open"}},{"submission_state":{"_eq":"api_only"}},{"external_program":{}}]},{"_not":{"external_program":{}}},{"_or":[{"_and":[{"state":{"_neq":"sandboxed"}},{"state":{"_neq":"soft_launched"}}]},{"external_program":{}}]}]},"first":25,"secureOrderBy":{"started_accepting_at":{"_direction":"DESC"}}},"query":"query DirectoryQuery($cursor: String, $secureOrderBy: FiltersTeamFilterOrder, $where: FiltersTeamFilterInput) {\n  me {\n    id\n    edit_unclaimed_profiles\n    h1_pentester\n    __typename\n  }\n  teams(first: 25, after: $cursor, secure_order_by: $secureOrderBy, where: $where) {\n    pageInfo {\n      endCursor\n      hasNextPage\n      __typename\n    }\n    edges {\n      node {\n        id\n        bookmarked\n        ...TeamTableResolvedReports\n        ...TeamTableAvatarAndTitle\n        ...TeamTableLaunchDate\n        ...TeamTableMinimumBounty\n        ...TeamTableAverageBounty\n        ...BookmarkTeam\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment TeamTableResolvedReports on Team {\n  id\n  resolved_report_count\n  __typename\n}\n\nfragment TeamTableAvatarAndTitle on Team {\n  id\n  profile_picture(size: medium)\n  name\n  handle\n  submission_state\n  triage_active\n  publicly_visible_retesting\n  state\n  external_program {\n    id\n    __typename\n  }\n  ...TeamLinkWithMiniProfile\n  __typename\n}\n\nfragment TeamLinkWithMiniProfile on Team {\n  id\n  handle\n  name\n  __typename\n}\n\nfragment TeamTableLaunchDate on Team {\n  id\n  started_accepting_at\n  __typename\n}\n\nfragment TeamTableMinimumBounty on Team {\n  id\n  currency\n  base_bounty\n  __typename\n}\n\nfragment TeamTableAverageBounty on Team {\n  id\n  currency\n  average_bounty_lower_amount\n  average_bounty_upper_amount\n  __typename\n}\n\nfragment BookmarkTeam on Team {\n  id\n  bookmarked\n  __typename\n}\n"}""".replace('\n',' \\n')

		try:
			response = session.post('https://hackerone.com/graphql',data=dataDirectory,headers=headers).json()
		except:
			print("[+] Retornando ao início...")
			continue

		for alvosEmPotencial in response['data']['teams']['edges']:

			

			if verificaAlvo(c, alvosEmPotencial['node']['id']):

				print("[+] O alvo não está no banco de dados...")
				insereAlvo(c,conn,alvosEmPotencial['node'])

				threading.Thread(target=notificaNovoAlvo, args=(alvosEmPotencial['node'],)).start()

			else:

				print("[+] O alvo já foi inserido no banco de dados...")

		sleep(30)
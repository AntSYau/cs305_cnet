import asyncio

async def dispatch(reader, writer):
	while True:
		data = await reader.readline()	# wait for request
		if data == b'exit\r\n':			# close connection if exit command received
			print("conn closed")
			break
		writer.write(data)				# write response
		print(data)
	await writer.drain()				# break operation
	writer.close()


loop = asyncio.get_event_loop()
listener=asyncio.start_server(dispatch, host='0.0.0.0', port=8080, loop=loop)	# listen on 8080
loop.run_until_complete(listener)
loop.run_forever()						# start server


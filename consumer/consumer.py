import redis

def message_handler(message):
    print(f"Received {message['data']}")

def main():
    redis_client = redis.Redis(host='redis', port=6379, db=0)
    pubsub = redis_client.pubsub()
    pubsub.subscribe(**{'booking_channel': message_handler})

    print('Waiting for messages. To exit press CTRL+C')
    pubsub.run_in_thread(sleep_time=0.001)

if __name__ == '__main__':
    main()

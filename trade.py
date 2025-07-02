
class Trade:
    def __init__(self, api_key, secret_key, passphrase):
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase

    def place_order(self, symbol, side, type_, size, price=None):
        return {
            "order_id": "mock_order_id",
            "status": "success",
            "symbol": symbol,
            "side": side,
            "type": type_,
            "size": size,
            "price": price
        }

import json

from browser_wrapper.propwire_api_client import PropwireClient


def print_section(title: str):
    """Print a section header"""
    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)


def example_property_search():
    """Example of searching for a property and getting its details"""
    client = PropwireClient()
    try:
        client.initialize()

        print_section("Property Search Example")

        # Search address
        address = "13912 W Pavillion Dr"
        print(f"\nSearching for address: {address}")
        properties = client.auto_complete(address)

        if not properties:
            print("No properties found")
            return

        # Get first property
        property = properties[0]
        print(f"\nFound property:")
        print(f"ID: {property.id}")
        print(f"Address: {property.address}")
        print(f"City: {property.city}, State: {property.state}")
        print(f"ZIP: {property.zip}")
        print(f"County: {property.county}")
        print(f"APN: {property.apn}")
        print(f"Coordinates: ({property.latitude}, {property.longitude})")

        # Get property details
        print("\nFetching property details...")
        details = client.get_property_details(property.id)
        print("\nProperty Details:")
        print(json.dumps(details, indent=2))

    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        client.cleanup()


def extract_phones_from_skip_trace(skip_trace_result) -> str:
    """Extract all phone numbers from skip trace response and return as comma-separated string"""

    try:
        # Navigate to phones array in the response
        phones = skip_trace_result['api_response']['output']['identity']['phones']

        # Extract formatted phone numbers (phoneDisplay)
        phone_numbers = [phone['phoneDisplay'] for phone in phones]

        # Join with commas
        phone_string = ', '.join(phone_numbers)

        print(f"Found phone numbers: {phone_string}")
        return phone_string

    except KeyError as e:
        print(f"Error extracting phones: Missing key {e}")
        return ""
    except Exception as e:
        print(f"Error processing phones: {str(e)}")
        return ""


def example_skip_trace():
    """Example of performing a skip trace"""
    client = PropwireClient()
    try:
        client.initialize()

        print_section("Skip Trace Example")

        # Search for property
        properties = client.auto_complete("1421 Aspen St, Selma, CA")
        if not properties:
            print("No properties found")
            return

        property = properties[0]
        print(f"\nFound property: {property.address}")

        # Mailing address for skip trace
        mail_address = {
            "address": "12043 S Elm Ave",
            "city": "Fresno",
            "state": "CA",
            "zip": "93706"
        }

        # Perform skip trace
        print("\nPerforming skip trace...")
        skip_trace_results = client.skip_trace_from_property(
            property
        )

        # print("\nSkip Trace Results:")
        # print(json.dumps(skip_trace_results, indent=2))

        # Extract phone numbers
        phone_numbers = extract_phones_from_skip_trace(skip_trace_results)
        print(f"\nExtracted phone numbers: {phone_numbers}")

    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        client.cleanup()


def example_multi_search():
    """Example of searching multiple addresses"""
    client = PropwireClient()
    try:
        client.initialize()

        print_section("Multiple Address Search Example")

        addresses = [
            "13912 W Pavillion Dr",
            "1421 Aspen St, Selma, CA",
            "12043 S Elm Ave, Fresno, CA"
        ]

        for address in addresses:
            print(f"\nSearching for: {address}")
            properties = client.auto_complete(address)

            if properties:
                property = properties[0]
                print(f"Found: {property.address}, {property.city}, {property.state}")
                print(f"ID: {property.id}")
                print(f"APN: {property.apn}")
            else:
                print("No properties found")

    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        client.cleanup()


if __name__ == "__main__":
    # print("\nRunning Property Search Example...")
    # example_property_search()

    print("\nRunning Skip Trace Example...")
    example_skip_trace()
    #
    # print("\nRunning Multi-Search Example...")
    # example_multi_search()


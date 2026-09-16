import Foundation

func fuzzyMatch(item: String, query: String) -> Bool {
    let itemLower = item.lowercased()
    let queryLower = query.lowercased()
    var itemIndex = itemLower.startIndex
    for queryChar in queryLower {
        guard let foundIndex = itemLower[itemIndex...].firstIndex(of: queryChar) else {
            return false
        }
        itemIndex = itemLower.index(after: foundIndex)
    }
    return true
}
